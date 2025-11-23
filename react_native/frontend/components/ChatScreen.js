import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function ChatScreen() {
  return (
    <View style={styles.page}>
      <Text style={styles.title}>AgriGuard Chat Assistant</Text>
      <Text style={styles.message}>Send a plant photo from the dashboard to begin chatting.</Text>
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
    marginBottom: 8,
  },
  message: {
    fontSize: 16,
    color: '#444',
    textAlign: 'center',
  },
});