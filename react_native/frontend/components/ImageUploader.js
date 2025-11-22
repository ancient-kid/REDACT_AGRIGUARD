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
import { uploadImage, sendForPrediction } from '../api';

export default function ImageUploader() {
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [validation, setValidation] = useState(null);
  const [analysis, setAnalysis] = useState(null);

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

  /** FULL PIPELINE → VALIDATION + ANALYSIS */
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
      Alert.alert("Success", "Analysis completed!");

    } catch (err) {
      Alert.alert("Error", String(err));
    }

    setLoading(false);
  };

  return (
    <ScrollView contentContainerStyle={styles.box}>

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
          <Text style={styles.header}>Image Validation</Text>
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
          <Text style={styles.header}>Prediction</Text>
          <Text>Class: {analysis.pred_class}</Text>
          <Text>Healthy: {(analysis.prob_healthy * 100).toFixed(1)}%</Text>
          <Text>Diseased: {(analysis.prob_diseased * 100).toFixed(1)}%</Text>

          <Text style={[styles.header, { marginTop: 10 }]}>Severity</Text>
          <Text>{analysis.severity}</Text>

          {analysis.summary && (
            <>
              <Text style={[styles.header, { marginTop: 10 }]}>Summary</Text>
              <Text>{analysis.summary}</Text>
            </>
          )}

          {analysis.recommendations?.length > 0 && (
            <>
              <Text style={[styles.header, { marginTop: 10 }]}>Recommendations</Text>
              {analysis.recommendations.map((r, i) => (
                <Text key={i}>• {r}</Text>
              ))}
            </>
          )}

          {analysis.shap_heatmap_base64 && (
            <>
              <Text style={[styles.header, { marginTop: 10 }]}>Explainability Map</Text>
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
  header: {
    fontWeight: "bold",
    fontSize: 16,
    marginBottom: 4,
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
