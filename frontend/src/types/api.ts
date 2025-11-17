export interface VoteRequest {
  option: 'cats' | 'dogs';
}

export interface VoteResponse {
  status: 'success' | 'error';
  message?: string;
}

export interface ResultsResponse {
  cats: number;
  dogs: number;
  total?: number;
}

export interface ApiError {
  message: string;
  status?: number;
}
