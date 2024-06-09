import React, { useState, useEffect } from 'react';
import { Button, FlatList, Pressable, SafeAreaView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons'

interface Task {
  id: number;
  text: string;
  completed: boolean;
}

export default function HomeScreen() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTask, setNewTask] = useState<string>('');

  useEffect(() => {
    // Load tasks function
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      // Load tasks from AsyncStorage
    } catch (error) {
      console.error(error);
    }
  };

  const saveTasks = async (newTasks: Task[]) => {
    try {
      // Save tasks to AsyncStorage
    } catch (error) {
      console.error(error);
    }
  };

  const addTask = () => {
    if (newTask.trim()) {
      const updatedTasks = [...tasks, { id: Date.now(), text: newTask, completed: false }];
      setTasks(updatedTasks);
      saveTasks(updatedTasks);
      setNewTask('');
    }
  };

  const toggleTaskCompletion = (id: number) => {
    const updatedTasks = tasks.map((task) =>
      task.id === id ? { ...task, completed: !task.completed } : task
    );
    setTasks(updatedTasks);
    saveTasks(updatedTasks);
  };

  const deleteTask = (id: number) => {
    const updatedTasks = tasks.filter((task) => task.id !== id);
    setTasks(updatedTasks);
    saveTasks(updatedTasks);
  };

  return (
    <SafeAreaView style={styles.container}>
     <View style={{padding:25}}>
     <Text style={styles.title}>To-Do List</Text>
      <TextInput
        style={styles.input}
        placeholder="Add a new task..."
        value={newTask}
        onChangeText={setNewTask}
      />
      <Pressable style={styles.addButton} onPress={addTask}>
        <Text style={styles.buttonText}>Add</Text>
      </Pressable>
      <FlatList
        data={tasks}
        renderItem={({ item }) => (
          <View style={styles.taskContainer}>
            <Text style={[styles.taskText, item.completed && styles.completedTask]}>{item.text}</Text>
            <View style={styles.iconsContainer}>
              <Pressable style={styles.iconButton} onPress={() => toggleTaskCompletion(item.id)}>
                <Ionicons name={item.completed ? 'close-circle' : 'checkmark'} style={styles.icon} />
              </Pressable>
              <Pressable style={styles.iconButton} onPress={() => deleteTask(item.id)}>
                <Ionicons name={'trash'} style={styles.icon} />
              </Pressable>
            </View>
          </View>
        )}
      />
     </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  title: {
    fontSize: 24,
    marginBottom: 10,
  },
  input: {
    backgroundColor: '#fff',
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 16,
    borderRadius: 8,
  },
  addButton: {
    backgroundColor: '#007bff',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 16,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
  },
  taskContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 5,
    backgroundColor: '#fff',
    padding: 10,
    borderRadius: 5,
    elevation: 2,
  },
  taskText: {
    flex: 1,
    textDecorationLine: 'none',
  },
  completedTask: {
    textDecorationLine: 'line-through',
  },
  iconsContainer: {
    flexDirection: 'row',
  },
  iconButton: {
    marginHorizontal: 10,
  },
  icon: {
    fontSize: 24,
    color: '#555',
  },
});
