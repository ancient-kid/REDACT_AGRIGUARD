import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function HistoryScreen() {
  return (
    <View style={styles.page}>
      <Text style={styles.title}>Analysis History</Text>
      <Text style={styles.message}>No uploads recorded yet.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  page: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#2d5016',
    marginBottom: 12,
  },
  message: {
    fontSize: 16,
    color: '#444',
  },
});