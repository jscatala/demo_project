import type { VoteRequest, VoteResponse, ResultsResponse, ApiError } from '../types/api';

const getApiBaseUrl = (): string => {
  const apiUrl = (window as any).APP_CONFIG?.API_URL;

  if (!apiUrl) {
    throw new Error('API URL not configured. Please check your configuration.');
  }

  return apiUrl;
};

const handleApiError = async (response: Response): Promise<ApiError> => {
  const status = response.status;

  let message = 'An unexpected error occurred';

  try {
    const data = await response.json();
    message = data.message || data.detail || message;
  } catch {
    // Response body is not JSON or empty
  }

  switch (status) {
    case 400:
      message = 'Invalid request. Please check your input.';
      break;
    case 404:
      message = 'Service not found. Please try again later.';
      break;
    case 422:
      message = 'Invalid vote option. Please select cats or dogs.';
      break;
    case 500:
      message = 'Server error. Please try again later.';
      break;
    case 503:
      message = 'Service temporarily unavailable. Please try again later.';
      break;
  }

  return { message, status };
};

export const postVote = async (option: 'cats' | 'dogs'): Promise<VoteResponse> => {
  try {
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl}/api/vote`;

    const request: VoteRequest = { option };

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await handleApiError(response);
      throw error;
    }

    const data = await response.json();
    return data as VoteResponse;
  } catch (error) {
    if (error instanceof Error && 'status' in error) {
      throw error;
    }

    if (error instanceof TypeError) {
      throw {
        message: 'Network error. Please check your connection.',
        status: 0,
      } as ApiError;
    }

    throw {
      message: error instanceof Error ? error.message : 'Failed to submit vote',
      status: 0,
    } as ApiError;
  }
};

export const getResults = async (): Promise<ResultsResponse> => {
  try {
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl}/api/results`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await handleApiError(response);
      throw error;
    }

    const data = await response.json();
    return data as ResultsResponse;
  } catch (error) {
    if (error instanceof Error && 'status' in error) {
      throw error;
    }

    if (error instanceof TypeError) {
      throw {
        message: 'Network error. Please check your connection.',
        status: 0,
      } as ApiError;
    }

    throw {
      message: error instanceof Error ? error.message : 'Failed to fetch results',
      status: 0,
    } as ApiError;
  }
};
