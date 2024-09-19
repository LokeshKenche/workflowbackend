from flask import Flask, jsonify
from flask_cors import CORS  # Import CORS
import requests
import time
import mlflow
from mlflow.tracking import MlflowClient
import sqlite3
import os
import numpy as np
from sklearn.ensemble import IsolationForest
import pandas as pd
import json
app = Flask(__name__)
class JSONReadError(Exception):
    pass
# Your Databricks Credentials and API URLs
databricks_token = "dapi885875a4c4b1a8bc94b0d20c477f99b2" 
job_id = "729004471699831" 
databricks_base_url = "https://dbc-634a6379-4489.cloud.databricks.com" 
# Set MLflow Tracking URI
mlflow.set_tracking_uri("databricks")

# Set Databricks Host and Token environment variables
os.environ['DATABRICKS_HOST'] = 'https://dbc-634a6379-4489.cloud.databricks.com' 
os.environ['DATABRICKS_TOKEN'] = databricks_token 


def readJson(file_path="data.json"):
    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        print(f"Successfully read JSON from {file_path}")
        return data
    except json.decoder.JSONDecodeError as e:
        print(f"Error decoding JSON from file: {e}")
        raise JSONReadError(f"Error decoding JSON from {file_path}: {e}")
# Function to create the database and table
def create_database():
    conn = sqlite3.connect('mlflow_metrics.db') 
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            duration REAL,
            cpu_usage REAL,
            memory_usage REAL,
            accuracy REAL
        )
    ''')
    conn.commit()
    conn.close()

# Call the function to create the database and table when the app starts
create_database()

# Root endpoint
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "API is up and running!"}), 200 

# @app.route('/current_metric',method=['GET']) 
# def current_metric():
# Endpoint to start Databricks workflow
@app.route('/start_workflow', methods=['POST'])
def start_workflow():
    databricks_url = f"{databricks_base_url}/api/2.1/jobs/run-now"
    headers = {"Authorization": f"Bearer {databricks_token}"}
    data = {"job_id": job_id}

    response = requests.post(databricks_url, headers=headers, json=data)

    if response.status_code == 200:
        run_data = response.json()
        run_id = run_data['run_id'] 
        return jsonify({"message": "Workflow started successfully!", "run_id": run_id}), 200
    else:
        return jsonify({"error": "Failed to start workflow", "details": response.text}), 500

# Endpoint to fetch MLflow logs and generate optimization suggestions
@app.route('/get_performance_metrics')
def get_performance_metrics():

    # Replace with your MLflow Experiment ID
    experiment_id = "2439024864367925"

    # Create MLflow client
    client = MlflowClient()

    # Search for all runs in the given experiment
    runs = client.search_runs(experiment_ids=[experiment_id], order_by=["attributes.start_time DESC"])

    # Process and format the data
    all_metrics_data = [] 
    latest_run_metrics = {}
    all_runs_metrics = []
    latest_run_timestamps = {}


    for run in runs:
        task_name = run.data.params.get('task_name')
        if task_name and task_name != 'performance_analysis': 
            metrics = {
                'task_name': task_name,
                'duration': round(run.data.metrics.get('duration', 0), 2), 
                'cpu_usage': round(run.data.metrics.get('cpu_usage', 0), 2), 
                'memory_usage': round(run.data.metrics.get('memory_usage', 0), 2),
                'accuracy': round(run.data.metrics.get('accuracy', 0), 2),
                'input_file_size': run.data.metrics.get('input_file_size', 0),  # Add new metrics
                'num_partitions': run.data.metrics.get('num_partitions', 0),
                'shuffle_read_bytes': run.data.metrics.get('shuffle_read_bytes', 0),
                'shuffle_write_bytes': run.data.metrics.get('shuffle_write_bytes', 0),
                'num_tasks': run.data.metrics.get('num_tasks', 0),
                'training_time': run.data.metrics.get('training_time', 0),
                'model_size': run.data.metrics.get('model_size', 0) 
            }
            all_metrics_data.append(metrics)
            all_runs_metrics.append(metrics)

            if task_name not in latest_run_timestamps or run.info.start_time > latest_run_timestamps[task_name]:
                latest_run_metrics[task_name] = metrics
                latest_run_timestamps[task_name] = run.info.start_time

 

    # Calculate average metrics
    avg_metrics_data = []
    for task_name in set(m['task_name'] for m in all_metrics_data):
        task_runs = [m for m in all_metrics_data if m['task_name'] == task_name]
        avg_metrics = {
            'task_name': task_name,
            'avg_duration': round(sum(m['duration'] for m in task_runs) / len(task_runs), 2),
            'avg_cpu_usage': round(sum(m['cpu_usage'] for m in task_runs) / len(task_runs), 2),
            'avg_memory_usage': round(sum(m['memory_usage'] for m in task_runs) / len(task_runs), 2),
            'avg_accuracy': round(sum(m['accuracy'] for m in task_runs if m['accuracy'] is not None) / len([m for m in task_runs if m['accuracy'] is not None]), 2) if any(m['accuracy'] is not None for m in task_runs) else None 
        }
        avg_metrics_data.append(avg_metrics)

    # Save all_runs_metrics to the database
    conn = sqlite3.connect('mlflow_metrics.db')
    cursor = conn.cursor()
    for metrics in all_runs_metrics:
        cursor.execute('''
            INSERT INTO metrics (task_name, duration, cpu_usage, memory_usage, accuracy) 
            VALUES (?, ?, ?, ?, ?)
        ''', (metrics['task_name'], metrics['duration'], metrics['cpu_usage'], metrics['memory_usage'], metrics['accuracy']))
    conn.commit()
    conn.close()

    df = pd.DataFrame(all_runs_metrics)
    df.fillna(0, inplace=True)

    thresholds = {} 
    for task_name in df['task_name'].unique():
        task_data = df[df['task_name'] == task_name][['duration', 'cpu_usage', 'memory_usage']]
        model = IsolationForest(contamination=0.05, random_state=42) 
        model.fit(task_data)
        anomaly_scores = model.decision_function(task_data)
        threshold = np.percentile(anomaly_scores, 95)
        thresholds[task_name] = {'duration': threshold, 'cpu_usage': threshold, 'memory_usage': threshold}


    for task_name, metrics in latest_run_metrics.items():
        suggestions = []
        # Data Loading suggestions
        if task_name == 'data_loading':
            if metrics['duration'] > thresholds[task_name]['duration']:
                if metrics.get('input_file_size', 0) > 100000000:  
                    suggestions.append("Data loading is taking longer than usual, and the dataset is large. Consider partitioning your data or using a more efficient file format.")
                else:
                    suggestions.append("Data loading is taking longer than usual. Consider optimizing file formats or increasing cluster resources.")
            if metrics['cpu_usage'] > thresholds[task_name]['cpu_usage']:
                suggestions.append("Review your data loading code for potential optimizations or consider increasing cluster CPU resources.")
            if metrics['memory_usage'] > thresholds[task_name]['memory_usage']:
                suggestions.append("Consider loading a sample of the data or increasing cluster memory.")

        # Preprocessing suggestions
        elif task_name == 'preprocessing':
            if metrics['duration'] > thresholds[task_name]['duration']:
                suggestions.append("Investigate potential bottlenecks in your preprocessing code or consider increasing cluster resources.")
            if metrics['cpu_usage'] > thresholds[task_name]['cpu_usage']:
                suggestions.append("Optimize computationally expensive preprocessing steps or consider increasing cluster CPU resources.")
            if metrics['memory_usage'] > thresholds[task_name]['memory_usage']:
                suggestions.append("Check for memory leaks or inefficient data structures in your preprocessing code. Consider increasing cluster memory or optimizing data handling.")

        # Transformation suggestions
        elif task_name == 'transformation':
            if metrics['duration'] > thresholds[task_name]['duration']:
                if metrics.get('shuffle_read_bytes', 0) + metrics.get('shuffle_write_bytes', 0) > 1000000000: 
                    suggestions.append("Transformation is taking longer than usual, potentially due to high shuffle volume. Consider optimizing data partitioning or using broadcast joins for smaller datasets.")
                elif metrics.get('num_tasks', 0) > 1000:  # Example high task count threshold
                    suggestions.append("Transformation is generating a large number of tasks, potentially indicating inefficient partitioning or excessive data shuffling. Consider optimizing your transformations.")
                else:
                    suggestions.append("Investigate potential bottlenecks in your transformation logic, such as complex joins or aggregations. Consider optimizing these operations or increasing cluster resources.")
            if metrics['cpu_usage'] > thresholds[task_name]['cpu_usage']:
                suggestions.append("Optimize computationally expensive transformations, such as UDFs or complex calculations. Consider increasing cluster CPU resources or using built-in Spark functions for better performance.")
            if metrics['memory_usage'] > thresholds[task_name]['memory_usage']:
                suggestions.append("Check for memory leaks or inefficient data structures in your transformation code. Consider caching intermediate DataFrames, adjusting Spark memory configuration, or increasing cluster memory.")

        # Model training suggestions
        elif task_name == 'model_training':
            if metrics['duration'] > thresholds[task_name]['duration']:
                if metrics.get('training_time', 0) / metrics['duration'] > 0.8:  # If training time dominates the task duration
                    suggestions.append("Model training itself is taking a long time. Consider reducing model complexity, using distributed training (if applicable), or increasing cluster resources.")
                else:
                    suggestions.append("Investigate potential bottlenecks in data preparation or other parts of the model training task.")
            if metrics['cpu_usage'] > thresholds[task_name]['cpu_usage']:
                suggestions.append("Optimize your model training code or consider increasing cluster CPU resources.")
            if metrics['memory_usage'] > thresholds[task_name]['memory_usage']:
                suggestions.append("Check for memory leaks or inefficient data structures in your model training code. Consider increasing cluster memory or using a more memory-efficient algorithm.")
            if 'accuracy' in metrics and metrics['accuracy'] < thresholds[task_name].get('accuracy', 0): 
                suggestions.append("Consider hyperparameter tuning, feature engineering, or trying a different algorithm to improve model performance.")

        latest_run_metrics[task_name]['suggestions'] = suggestions
    

    # Train Isolation Forest models and generate suggestions (You'll need to implement this part)
    # ... (Code to train Isolation Forest models and set thresholds)
    # ... (Code to generate suggestions based on thresholds and latest_run_metrics)

    response=jsonify({
        "all_runs_avg_metrics": avg_metrics_data, 
        "latest_run_metrics": latest_run_metrics,
        "all_runs_metrics": all_runs_metrics ,
         "pastData":readJson()
    })
    writeJson(latest_run_metrics) 
    return response
@app.route('/get_historical_metrics')
def get_historical_metrics():
    conn = sqlite3.connect('mlflow_metrics.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM metrics')
    rows = cursor.fetchall()
    # print(rows[0])
    conn.close()

    # Process the rows into a suitable format (e.g., a list of dictionaries)
    historical_metrics = [] 
    for row in rows:
        historical_metrics.append({
            'id': row[0],
            'task_name': row[1],
            'duration': row[2],
            'cpu_usage': row[3],
            'memory_usage': row[4],
            'accuracy': row[5]
        })

    return jsonify(historical_metrics)

if __name__ == '__main__':
    app.run(debug=True)

