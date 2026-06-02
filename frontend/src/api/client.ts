/**
 * Axios HTTP client instance.
 * Base URL configured via VITE_API_BASE_URL environment variable.
 */

import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api";

const client = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

export default client;
