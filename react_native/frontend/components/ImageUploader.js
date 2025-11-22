import React, { useState } from 'react';
import {
  View,
  Text,
  Button,
  Image,
  ActivityIndicator,
  StyleSheet,
  Alert,
  ScrollView,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { uploadImage, sendForPrediction, createUpload } from '../api';

export default function ImageUploader({ route, navigation }) {
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [validation, setValidation] = useState(null);
  const [analysis, setAnalysis] = useState(null);

  // If coming from history, load existing data
  React.useEffect(() => {
    if (route?.params?.uploadData) {
      // Load existing upload data (you could fetch the image here)
      const uploadData = route.params.uploadData;
      setAnalysis({
        pred_class: uploadData.predictionClass,
        prob_healthy: uploadData.confidence.healthy,
        prob_diseased: uploadData.confidence.diseased,
        severity: uploadData.severity,
        summary: uploadData.summary,
      });
    }
  }, [route]);

  /** PICK FROM GALLERY (Samsung-safe) */
  const pickImage = async () => {
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
    });

    if (!res.canceled) {
      setImage({ uri: res.assets[0].uri });
      setValidation(null);
      setAnalysis(null);
    }
  };

  /** CAPTURE USING CAMERA */
  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") {
      Alert.alert("Permission required", "Camera access is needed.");
      return;
    }

    const res = await ImagePicker.launchCameraAsync({
      quality: 1,
      allowsEditing: true,
    });

    if (!res.canceled) {
      setImage({ uri: res.assets[0].uri });
      setValidation(null);
      setAnalysis(null);
    }
  };

  /** FULL PIPELINE → VALIDATION + ANALYSIS + SAVE */
  const runAnalysis = async () => {
    if (!image) return Alert.alert("Pick an image first");

    setLoading(true);
    setValidation(null);
    setAnalysis(null);

    try {
      // STEP 1: Validate
      const valid = await uploadImage(image.uri);
      setValidation(valid);

      const ok =
        valid.not_corrupted &&
        valid.format_valid &&
        valid.not_empty &&
        !valid.visual_corruption &&
        valid.errors.length === 0;

      if (!ok) {
        Alert.alert("Invalid Image", "Image validation failed.");
        setLoading(false);
        return;
      }

      // STEP 2: AI Pipeline
      const result = await sendForPrediction(image.uri);
      setAnalysis(result);

      // STEP 3: Save to backend
      if (global.currentUser) {
        const filename = image.uri.split('/').pop();
        await createUpload({
          user_id: global.currentUser.user_id,
          file_name: filename,
          image_path: image.uri, // In production, you'd upload to server first
          prediction_class: result.pred_class,
          severity: result.severity || 'Unknown',
          confidence_healthy: result.prob_healthy,
          confidence_diseased: result.prob_diseased,
          summary: result.summary || 'Analysis completed',
        });
      }

      Alert.alert("Success", "Analysis completed and saved!");

    } catch (err) {
      Alert.alert("Error", String(err));
    }

    setLoading(false);
  };

  return (
    <ScrollView contentContainerStyle={styles.box}>

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Plant Disease Analysis</Text>
        <Text style={styles.subtitle}>Upload or capture a plant image</Text>
      </View>

      {/* Preview */}
      {image ? (
        <Image source={{ uri: image.uri }} style={styles.preview} />
      ) : (
        <View style={styles.placeholder}>
          <Text>No image selected</Text>
        </View>
      )}

      {/* Gallery + Camera */}
      <Button title="Pick Image from Gallery" onPress={pickImage} />
      <View style={{ height: 8 }} />
      <Button title="Take Photo" onPress={takePhoto} />
      <View style={{ height: 12 }} />

      {/* Full Pipeline Button */}
      <Button
        title="Run Full Analysis"
        onPress={runAnalysis}
        disabled={loading}
      />

      {loading && <ActivityIndicator style={{ marginTop: 12 }} />}

      {/* SECTION 1 — VALIDATION */}
      {validation && (
        <View style={styles.section}>
          <Text style={styles.headerText}>Image Validation</Text>
          <Text>Not corrupted: {String(validation.not_corrupted)}</Text>
          <Text>Format valid: {String(validation.format_valid)}</Text>
          <Text>Not empty: {String(validation.not_empty)}</Text>
          <Text>Visual corruption: {String(validation.visual_corruption)}</Text>
          <Text style={{ marginTop: 4 }}>SHA256:</Text>
          <Text style={styles.hash}>{validation.hash}</Text>
        </View>
      )}

      {/* SECTION 2 — ANALYSIS RESULTS */}
      {analysis && (
        <View style={styles.section}>
          <Text style={styles.headerText}>Prediction Results</Text>
          <View style={styles.resultCard}>
            <Text style={styles.prediction}>
              {analysis.pred_class === 'HEALTHY' ? '🌱 Healthy Plant' : '⚠️ Diseased Plant'}
            </Text>
            <Text style={styles.confidence}>
              Healthy: {(analysis.prob_healthy * 100).toFixed(1)}%
            </Text>
            <Text style={styles.confidence}>
              Diseased: {(analysis.prob_diseased * 100).toFixed(1)}%
            </Text>
          </View>

          <Text style={[styles.headerText, { marginTop: 10 }]}>Severity</Text>
          <Text style={styles.severity}>{analysis.severity}</Text>

          {analysis.summary && (
            <>
              <Text style={[styles.headerText, { marginTop: 10 }]}>Summary</Text>
              <Text style={styles.summary}>{analysis.summary}</Text>
            </>
          )}

          {analysis.recommendations?.length > 0 && (
            <>
              <Text style={[styles.headerText, { marginTop: 10 }]}>Recommendations</Text>
              {analysis.recommendations.map((r, i) => (
                <Text key={i} style={styles.recommendation}>• {r}</Text>
              ))}
            </>
          )}

          {analysis.shap_heatmap_base64 && (
            <>
              <Text style={[styles.headerText, { marginTop: 10 }]}>Explainability Map</Text>
              <Image
                source={{
                  uri: `data:image/png;base64,${analysis.shap_heatmap_base64}`,
                }}
                style={styles.shapImg}
              />
            </>
          )}
        </View>
      )}

    </ScrollView>
  );
}

const styles = StyleSheet.create({
  box: {
    padding: 12,
    alignItems: "center"
  },
  header: {
    width: '100%',
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2d5016',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  preview: {
    width: 260,
    height: 260,
    borderRadius: 12,
    backgroundColor: "#eee",
    marginBottom: 12,
  },
  placeholder: {
    width: 260,
    height: 260,
    backgroundColor: "#ddd",
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  section: {
    width: "100%",
    backgroundColor: "#fff",
    padding: 14,
    borderRadius: 10,
    marginTop: 14,
    elevation: 2,
  },
  headerText: {
    fontWeight: "bold",
    fontSize: 18,
    color: '#2d5016',
    marginBottom: 8,
  },
  resultCard: {
    backgroundColor: '#f8f9fa',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  prediction: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2d5016',
    marginBottom: 8,
  },
  confidence: {
    fontSize: 16,
    color: '#555',
    marginBottom: 4,
  },
  severity: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#f57c00',
  },
  summary: {
    fontSize: 16,
    color: '#333',
    lineHeight: 22,
  },
  recommendation: {
    fontSize: 14,
    color: '#555',
    marginBottom: 4,
    lineHeight: 20,
  },
  hash: {
    fontSize: 12,
    color: "#555",
    marginTop: 4,
  },
  shapImg: {
    width: "100%",
    height: 250,
    borderRadius: 10,
    marginTop: 8,
  },
});
