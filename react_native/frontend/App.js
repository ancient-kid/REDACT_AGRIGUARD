import React from 'react';
import { SafeAreaView, StyleSheet, Text, View } from 'react-native';
import ImageUploader from './components/ImageUploader';

export default function App() {
  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>AgriGuard</Text>
      <View style={styles.content}>
        <ImageUploader />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f6f9f3',
    alignItems: 'center',
    justifyContent: 'flex-start',
  },
  title: {
    marginTop: 24,
    fontSize: 20,
    fontWeight: '700'
  },
  content: {
    width: '95%',
    marginTop: 12
  }
});
