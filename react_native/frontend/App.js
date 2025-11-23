import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import LoginScreen from './components/LoginScreen';
import DashboardScreen from './components/DashboardScreen';
import ImageUploader from './components/ImageUploader';
import HistoryScreen from './components/HistoryScreen';
import ChatScreen from './components/ChatScreen';

const Stack = createStackNavigator();

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Login"
          screenOptions={{
            headerStyle: {
              backgroundColor: '#2d5016',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
          }}
        >
          <Stack.Screen
            name="Login"
            component={LoginScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Dashboard"
            component={DashboardScreen}
            options={{
              title: 'AgriGuard Dashboard',
              headerLeft: null, // Prevent going back to login
            }}
          />
          <Stack.Screen
            name="Analysis"
            component={ImageUploader}
            options={{
              title: 'Plant Analysis',
            }}
          />
          <Stack.Screen
            name="History"
            component={HistoryScreen}
            options={{
              title: 'Analysis History',
            }}
          />
          <Stack.Screen
            name="Chat"
            component={ChatScreen}
            options={{
              title: 'Plant Disease Assistant',
            }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}