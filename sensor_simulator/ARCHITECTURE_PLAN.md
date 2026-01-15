# Sensor Simulator Architecture Plan

This document outlines the plan for refactoring the sensor simulator to be more realistic, modular, and scalable.

## 1. Goal

The primary goal is to simulate a realistic data pipeline for a "Mega Fulfillment Center". This involves:
- Generating raw, signal-like data from a large number of individual sensors.
- Aggregating this raw data into meaningful, zone-level insights.
- Transmitting the aggregated data to the frontend for real-time visualization.

## 2. Proposed Architecture

The new architecture will consist of three main components, separating the different concerns of the data pipeline:

### a. Sensor Generator (`sensor_generator.py`)
- **Responsibility:** Generate fine-grained, raw sensor data ("signals").
- **Logic:**
    - It will use an expanded `ZONES_CONFIG` that models a large-scale fulfillment center.
    - It will loop through every individual sensor (e.g., temperature, vibration, load cell on each line) and generate a single reading with a timestamp.
    - **Output Format (Example Signal):** `{"timestamp": "...", "sensor_id": "sensor-PK-01-temp-01", "value": 35.4}`

### b. Aggregator (`aggregator.py`)
- **Responsibility:** Consume raw sensor signals and produce aggregated, zone-level data.
- **Logic:**
    - It will receive the raw signals from the `sensor_generator`.
    - It will maintain an in-memory state of all zones.
    - As new signals arrive, it will update the state for the corresponding zone (e.g., update the running average for temperature).
    - Periodically (e.g., every 3 seconds), it will format its current state into the structure defined by `zone_data_schema.json`.
    - **Output:** An array of zone objects, ready for the frontend.

### c. Producer (`producers.py` & `websocket_server.py`)
- **Responsibility:** Transmit the aggregated data to the frontend.
- **Logic:**
    - The `Aggregator` will pass its final aggregated data array to the `WebSocketProducer`.
    - The existing WebSocket server will broadcast this array to all connected frontend clients.

## 3. Data Flow

The end-to-end data flow will be:

`sensor_generator` -> `(Raw Sensor Signal)` -> `aggregator` -> `(Aggregated Zone JSON Array)` -> `WebSocketProducer` -> `Frontend`

## 4. Implementation Steps

1.  **Save Plan:** Save this architectural plan to a file.
2.  **Expand Zones:** Update `ZONES_CONFIG` to a "Mega Fulfillment Center" scale.
3.  **Implement `sensor_generator.py`:** Create the new script for raw signal generation.
4.  **Implement `aggregator.py`:** Create the new script for consuming signals and aggregating data.
5.  **Orchestrate:** Refactor the main execution logic (`main.py`) to run the generator and aggregator together.
6.  **Verify:** Ensure the frontend correctly receives and displays the data from the new pipeline.
