# Restaurant Booking API Documentation

Complete API documentation for the Restaurant Booking System with voice agent integration.

## Table of Contents

- [Getting Started](#getting-started)
- [Postman Collection](#postman-collection)
- [API Endpoints](#api-endpoints)
  - [Health & Info](#health--info)
  - [Weather](#weather)
  - [Bookings](#bookings)
  - [Tools](#tools)
  - [LiveKit](#livekit)
- [Data Formats](#data-formats)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Getting Started

### Prerequisites

- Node.js and npm installed
- MongoDB database running
- Environment variables configured (see `.env.example`)

### Base URL

- **Development**: `http://localhost:5000`
- **Production**: Configure as needed

## Postman Collection

### Import Instructions

1. **Import Collection**:

   - Open Postman
   - Click "Import" button
   - Select `Restaurant_Booking_API.postman_collection.json`
   - Collection will be imported with all endpoints and examples

2. **Import Environment** (Optional):

   - Click "Import" in Postman
   - Select `Restaurant_Booking_API.postman_environment.json`
   - Select the environment from the dropdown to use variables

3. **Configure Environment Variables**:
   - Update `base_url` if your server runs on a different port/host
   - Other variables are optional and can be set as needed

### Collection Structure

The collection is organized into folders:

- **Health & Info**: System health and API information
- **Weather**: Weather forecast endpoints
- **Bookings**: Booking management endpoints
- **Tools**: Tool execution endpoints (used by voice agent)
- **LiveKit**: LiveKit token generation for voice agent

## API Endpoints

### Health & Info

#### GET `/api/health`

Check the health status of the API and its services.

**Response**:

```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "services": {
    "server": "running",
    "mongodb": "connected",
    "email": "configured"
  }
}
```

#### GET `/`

Get API information and available endpoints.

**Response**:

```json
{
  "message": "Restaurant Booking API",
  "version": "1.0.0",
  "endpoints": {
    "bookings": "/api/bookings",
    "weather": "/api/weather/:date",
    "health": "/api/health"
  }
}
```

### Weather

#### GET `/api/weather/:date`

Fetch weather forecast for a specific date and optionally time.

**Path Parameters**:

- `date` (required): Date in `YYYY-MM-DD` format (e.g., `2024-01-20`)

**Query Parameters**:

- `time` (optional): Time in `HH:mm` format (24-hour, e.g., `19:00` for 7 PM)

**Example**:

```
GET /api/weather/2024-01-20?time=19:00
```

**Response**:

```json
{
  "success": true,
  "data": {
    "date": "2024-01-20",
    "time": "19:00",
    "location": "Mumbai",
    "condition": "Clear",
    "temperature": 28,
    "description": "clear sky",
    "humidity": 65,
    "windSpeed": 3.5
  }
}
```

**Note**: Location defaults to Mumbai. Configure via `RESTAURANT_LOCATION` environment variable.

### Bookings

#### POST `/api/bookings`

Create a new restaurant booking.

**Request Body**:

```json
{
  "numberOfGuests": 4,
  "bookingDate": "2024-01-20",
  "bookingTime": "19:00",
  "cuisinePreference": "Italian",
  "specialRequests": "Window seat preferred",
  "seatingPreference": "indoor",
  "customerName": "John Doe",
  "customerEmail": "john.doe@example.com",
  "customerContact": "+1234567890"
}
```

**Required Fields**:

- `numberOfGuests` (number): Number of guests (min: 1)
- `bookingDate` (string): Date in `YYYY-MM-DD` format
- `bookingTime` (string): Time in `HH:mm` format (24-hour)

**Optional Fields**:

- `cuisinePreference` (string): Cuisine type preference
- `specialRequests` (string): Special requests or dietary restrictions
- `seatingPreference` (string): `"indoor"` or `"outdoor"` (case-insensitive, defaults to `"indoor"`)
- `customerName` (string): Customer name (defaults to `"Guest"`)
- `customerEmail` (string): Email for confirmation
- `customerContact` (string): Contact number

**Response** (201 Created):

```json
{
  "success": true,
  "data": {
    "_id": "65a1b2c3d4e5f6g7h8i9j0k1",
    "bookingId": "65a1b2c3d4e5f6g7h8i9j0k1",
    "customerName": "John Doe",
    "numberOfGuests": 4,
    "bookingDate": "2024-01-20T00:00:00.000Z",
    "bookingTime": "19:00",
    "seatingPreference": "indoor",
    "status": "pending"
  }
}
```

#### GET `/api/bookings`

Retrieve all bookings sorted by creation date (newest first).

**Response**:

```json
{
  "success": true,
  "count": 2,
  "data": [...]
}
```

#### GET `/api/bookings/:id`

Retrieve a specific booking by its MongoDB ObjectId.

**Path Parameters**:

- `id` (required): MongoDB ObjectId of the booking

**Response**:

```json
{
  "success": true,
  "data": {
    "_id": "65a1b2c3d4e5f6g7h8i9j0k1",
    "bookingId": "65a1b2c3d4e5f6g7h8i9j0k1",
    "customerName": "John Doe",
    "numberOfGuests": 4,
    "bookingDate": "2024-01-20T00:00:00.000Z",
    "bookingTime": "19:00",
    "status": "pending"
  }
}
```

#### DELETE `/api/bookings/:id`

Cancel a booking by setting its status to `"cancelled"`.

**Path Parameters**:

- `id` (required): MongoDB ObjectId of the booking to cancel

**Response**:

```json
{
  "success": true,
  "data": {
    "_id": "65a1b2c3d4e5f6g7h8i9j0k1",
    "status": "cancelled"
  },
  "message": "Booking cancelled successfully"
}
```

#### GET `/api/bookings/availability`

Check if a date/time slot is available for booking.

**Query Parameters**:

- `date` (required): Date in `YYYY-MM-DD` format
- `time` (optional): Time in `HH:mm` format (24-hour). If provided, checks exact time slot. If omitted, checks entire date.

**Example**:

```
GET /api/bookings/availability?date=2024-01-20&time=19:00
```

**Response**:

```json
{
  "success": true,
  "data": {
    "available": true,
    "date": "2024-01-20",
    "time": "19:00",
    "existingBookings": 0
  }
}
```

### Tools

Tools are primarily used by the voice agent but can be called directly via API.

#### GET `/api/tools`

Get a list of all available tools with their names and descriptions.

**Response**:

```json
{
  "success": true,
  "data": [
    {
      "name": "weather",
      "description": "Get weather forecast for a specific date and optionally time"
    },
    {
      "name": "check-availability",
      "description": "Check if a date/time slot is available for booking"
    },
    {
      "name": "send-email",
      "description": "Send booking confirmation email"
    },
    {
      "name": "create-booking",
      "description": "Create a new restaurant booking"
    },
    {
      "name": "check-date",
      "description": "Get current date and time for context awareness"
    }
  ]
}
```

#### POST `/api/tools/:toolName`

Execute a specific tool.

**Path Parameters**:

- `toolName` (required): Name of the tool to execute

**Available Tools**:

1. **`check-date`**: Get current date and time

   ```json
   {}
   ```

2. **`weather`**: Get weather forecast

   ```json
   {
     "date": "2024-01-20",
     "time": "19:00",
     "location": "Mumbai"
   }
   ```

3. **`check-availability`**: Check availability

   ```json
   {
     "date": "2024-01-20",
     "time": "19:00"
   }
   ```

4. **`create-booking`**: Create booking

   ```json
   {
     "numberOfGuests": 4,
     "bookingDate": "2024-01-20",
     "bookingTime": "19:00",
     "seatingPreference": "indoor"
   }
   ```

5. **`send-email`**: Send confirmation email
   ```json
   {
     "bookingId": "65a1b2c3d4e5f6g7h8i9j0k1"
   }
   ```

**Response**:

```json
{
  "success": true,
  "data": {...}
}
```

### LiveKit

#### POST `/api/livekit/token`

Generate a LiveKit access token for frontend connection to voice agent room.

**Request Body**:

```json
{
  "roomName": "restaurant-booking-1234567890",
  "participantName": "user-1234567890"
}
```

**Required Fields**:

- `roomName` (string): Unique room identifier
- `participantName` (string): Participant identifier

**Response**:

```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Note**: Requires `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` environment variables.

## Data Formats

### Date Format

- Format: `YYYY-MM-DD`
- Example: `2024-01-20`

### Time Format

- Format: `HH:mm` (24-hour)
- Examples: `19:00` (7 PM), `09:30` (9:30 AM)

### Seating Preference

- Valid values: `"indoor"` or `"outdoor"` (case-insensitive)
- Default: `"indoor"`
- **Note**: The API automatically normalizes seating preference to lowercase, so `"Indoor"`, `"INDOOR"`, and `"indoor"` are all accepted.

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message description"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate booking)
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service degraded (health check)

## Examples

### Complete Booking Flow

1. **Check Availability**:

   ```
   GET /api/bookings/availability?date=2024-01-20&time=19:00
   ```

2. **Check Weather** (optional, for seating suggestion):

   ```
   GET /api/weather/2024-01-20?time=19:00
   ```

3. **Create Booking**:

   ```
   POST /api/bookings
   {
     "numberOfGuests": 4,
     "bookingDate": "2024-01-20",
     "bookingTime": "19:00",
     "seatingPreference": "indoor",
     "customerName": "John Doe",
     "customerEmail": "john.doe@example.com"
   }
   ```

4. **Send Confirmation Email** (optional):
   ```
   POST /api/tools/send-email
   {
     "bookingId": "65a1b2c3d4e5f6g7h8i9j0k1"
   }
   ```

### Using Tools (Voice Agent)

The voice agent uses tools via the `/api/tools/:toolName` endpoint:

1. **Get Current Date/Time**:

   ```
   POST /api/tools/check-date
   {}
   ```

2. **Check Weather**:

   ```
   POST /api/tools/weather
   {
     "date": "2024-01-20",
     "time": "19:00"
   }
   ```

3. **Create Booking**:
   ```
   POST /api/tools/create-booking
   {
     "numberOfGuests": 4,
     "bookingDate": "2024-01-20",
     "bookingTime": "19:00",
     "seatingPreference": "indoor"
   }
   ```

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Seating preference is case-insensitive and automatically normalized
- Email confirmation is sent automatically when creating bookings via the tool endpoint if `customerEmail` is provided
- The API uses MongoDB ObjectIds for booking identifiers
- All date/time validations use 24-hour format

## Support

For issues or questions, please refer to the project repository or contact the development team.
