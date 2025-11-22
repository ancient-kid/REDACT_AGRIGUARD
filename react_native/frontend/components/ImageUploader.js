import React, { useState, useEffect } from 'react';
import { View, Text, Button, Image, ActivityIndicator, StyleSheet, Alert } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { uploadImage, sendForPrediction } from '../api';

export default function ImageUploader() {
  const [image, setImage] = useState(null); // { uri }
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    (async () => {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission required', 'Camera roll permission is required to select images.');
      }
    })();
  }, []);

  const pickImage = async () => {
    let res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });

    if (!res.canceled) {
      setImage({ uri: res.assets[0].uri });
      setResult(null);
    }
  };

  const handleValidation = async () => {
    if (!image) return Alert.alert("Pick an image first");

    setLoading(true);
    try {
      const response = await uploadImage(image.uri);
      setResult(response);
    } catch (err) {
      Alert.alert("Error", String(err));
    } finally {
      setLoading(false);
    }
  };

  const handlePrediction = async () => {
    if (!image) return Alert.alert("Pick an image first");

    setLoading(true);
    try {
      const response = await sendForPrediction(image.uri);
      Alert.alert(
        "Prediction",
        `Label: ${response.label}\nConfidence: ${response.confidence}\nRecommendation: ${response.recommendation}`
      );
    } catch (err) {
      Alert.alert("Error", String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.box}>
      {image ? (
        <Image source={{ uri: image.uri }} style={styles.preview} />
      ) : (
        <View style={styles.placeholder}><Text>No image selected</Text></View>
      )}

      <Button title="Pick Image" onPress={pickImage} />
      <View style={{ height: 8 }} />

      <Button title="Validate Image" onPress={handleValidation} disabled={loading} />
      <View style={{ height: 8 }} />

      <Button title="Predict Disease" onPress={handlePrediction} disabled={loading} />

      {loading && <ActivityIndicator style={{ marginTop: 12 }} />}

      {result && (
        <View style={styles.resultBox}>
          <Text style={{ fontWeight: "bold" }}>Validation Results</Text>
          <Text>Not corrupted: {String(result.not_corrupted)}</Text>
          <Text>Format valid: {String(result.format_valid)}</Text>
          <Text>SHA256: {result.hash}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  box: { padding: 12 },
  preview: { width: 250, height: 250, borderRadius: 10, backgroundColor: '#eee' },
  placeholder: {
    width: 250,
    height: 250,
    backgroundColor: '#e8e8e8',
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center'
  },
  resultBox: {
    marginTop: 15,
    padding: 12,
    backgroundColor: "#fff",
    borderRadius: 10
  }
});
