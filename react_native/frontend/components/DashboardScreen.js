import React from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';

export default function DashboardScreen({ navigation }) {
  return (
    <View style={styles.page}>
      <Text style={styles.title}>Welcome to AgriGuard</Text>
      <Text style={styles.subtitle}>Record and analyze a new plant photo</Text>
      <View style={styles.section}>
        <Button title="New Analysis" onPress={() => navigation.navigate('Analysis')} />
      </View>
      <View style={styles.section}>
        <Button title="History" onPress={() => navigation.navigate('History')} />
      </View>
      <View style={styles.section}>
        <Button title="Chat Assistant" onPress={() => navigation.navigate('Chat')} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  page: {
    flex: 1,
    padding: 24,
    backgroundColor: '#fff',
    justifyContent: 'center',
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#2d5016',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    textAlign: 'center',
    fontSize: 16,
    color: '#666',
    marginBottom: 24,
  },
  section: {
    marginBottom: 12,
  },
});