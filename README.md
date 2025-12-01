# User Authentication API

A robust Node.js and Express.js RESTful API for user authentication with MongoDB as the database. This project provides a secure and scalable authentication system that can be integrated with various applications.

## Project Description

This API provides comprehensive user authentication functionality including:

- User registration and account creation
- Secure login with JWT (JSON Web Tokens)
- Password encryption with bcrypt
- Role-based access control
- Password reset functionality
- Account verification
- Session management

The system is built with security best practices in mind and follows a modular architecture for easy extension and maintenance.

## Technology Stack

- **Backend**: Node.js, Express.js
- **Database**: MongoDB
- **Authentication**: JWT (JSON Web Tokens), bcrypt
- **Validation**: Joi/express-validator
- **Testing**: Jest, Supertest

## Setup Instructions

### Prerequisites

- Node.js (v14 or higher)
- MongoDB (local installation or MongoDB Atlas account)
- npm or yarn package manager

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd user-auth
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Environment Configuration:
   Create a `.env` file in the root directory with the following variables:
   ```
   PORT=3000
   MONGODB_URI=mongodb://localhost:27017/user-auth
   JWT_SECRET=your_jwt_secret_key
   JWT_EXPIRATION=1h
   NODE_ENV=development
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

5. The API will be available at `http://localhost:3000`

### Project Structure

```
user-auth/
├── src/
│   ├── config/         # Configuration files
│   ├── controllers/    # Request handlers
│   ├── middleware/     # Express middlewares
│   ├── models/         # Database models
│   ├── routes/         # API routes
│   ├── services/       # Business logic
│   ├── utils/          # Utility functions
│   └── app.js          # Express app setup
├── .env                # Environment variables
├── .gitignore          # Git ignore file
├── package.json        # Project dependencies
├── README.md           # Project documentation
└── server.js           # Application entry point
```

## Usage Examples

### User Registration

```javascript
// Client-side example with fetch API
const registerUser = async (userData) => {
  try {
    const response = await fetch('http://localhost:3000/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Registration error:', error);
  }
};

// Example usage
const userData = {
  username: 'johndoe',
  email: 'john.doe@example.com',
  password: 'securePassword123',
};

registerUser(userData)
  .then(response => console.log('Registration successful:', response))
  .catch(error => console.error(error));
```

### User Login

```javascript
// Client-side example with fetch API
const loginUser = async (credentials) => {
  try {
    const response = await fetch('http://localhost:3000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    const data = await response.json();

    // Store the token in localStorage or a more secure storage
    if (data.token) {
      localStorage.setItem('authToken', data.token);
    }

    return data;
  } catch (error) {
    console.error('Login error:', error);
  }
};

// Example usage
const credentials = {
  email: 'john.doe@example.com',
  password: 'securePassword123',
};

loginUser(credentials)
  .then(response => console.log('Login successful:', response))
  .catch(error => console.error(error));
```

### Making Authenticated Requests

```javascript
// Client-side example with fetch API
const fetchProtectedResource = async () => {
  try {
    const token = localStorage.getItem('authToken');

    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch('http://localhost:3000/api/users/profile', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching protected resource:', error);
  }
};

fetchProtectedResource()
  .then(response => console.log('Protected data:', response))
  .catch(error => console.error(error));
```

## API Endpoints

| Method | Endpoint                  | Description                  | Authentication Required |
|--------|---------------------------|------------------------------|-------------------------|
| POST   | /api/auth/register        | Register a new user          | No                      |
| POST   | /api/auth/login           | Authenticate user            | No                      |
| GET    | /api/users/profile        | Get user profile             | Yes                     |
| PUT    | /api/users/profile        | Update user profile          | Yes                     |
| POST   | /api/auth/forgot-password | Request password reset       | No                      |
| POST   | /api/auth/reset-password  | Reset password with token    | No                      |
| GET    | /api/users                | Get all users (Admin only)   | Yes + Admin Role        |

## Testing

Run the test suite with:

```bash
npm test
```

For testing specific components:

```bash
npm test -- --testPathPattern=auth
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.