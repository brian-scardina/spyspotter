import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

export interface ScanRequest {
  url: string;
  scan_type: 'basic' | 'enhanced';
  enable_javascript?: boolean;
  enable_ml_analysis?: boolean;
  enable_advanced_fingerprinting?: boolean;
}

export interface ScanResponse {
  scan_id: string;
  status: string;
  message: string;
  estimated_duration?: number;
}

export interface ScanResult {
  scan_id: string;
  url: string;
  status: string;
  timestamp: string;
  tracker_count: number;
  privacy_score?: number;
  risk_level?: string;
  scan_duration?: number;
  trackers: any[];
  performance_metrics: any;
  privacy_analysis: any;
  error?: string;
}

export interface Statistics {
  total_scans: number;
  total_trackers_found: number;
  avg_privacy_score: number;
  most_common_trackers: Array<{
    name: string;
    count: number;
    percentage: number;
  }>;
  risk_distribution: Record<string, number>;
  daily_scan_count: Array<{
    date: string;
    count: number;
  }>;
}

export class WebSocketService {
  private socket: WebSocket | null = null;
  private listeners: Map<string, (data: any) => void> = new Map();

  connect(scanId: string): Promise<WebSocket> {
    return new Promise((resolve, reject) => {
      const wsUrl = `ws://localhost:8000/ws/scan/${scanId}`;
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        resolve(this.socket!);
      };

      this.socket.onerror = (error) => {
        reject(error);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.listeners.forEach((callback) => callback(data));
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.socket.onclose = () => {
        this.socket = null;
      };
    });
  }

  onMessage(id: string, callback: (data: any) => void) {
    this.listeners.set(id, callback);
  }

  removeListener(id: string) {
    this.listeners.delete(id);
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.listeners.clear();
  }
}

export const apiService = {
  // Scan operations
  createScan: async (request: ScanRequest): Promise<ScanResponse> => {
    const response = await api.post('/scan', request);
    return response.data;
  },

  getScanResult: async (scanId: string): Promise<ScanResult> => {
    const response = await api.get(`/scan/${scanId}`);
    return response.data;
  },

  getResults: async (params?: {
    limit?: number;
    offset?: number;
    url?: string;
    risk_level?: string;
  }): Promise<ScanResult[]> => {
    const response = await api.get('/results', { params });
    return response.data;
  },

  getReport: async (scanId: string, format: 'json' | 'html' | 'pdf' = 'json'): Promise<any> => {
    const response = await api.get(`/reports/${scanId}`, {
      params: { format }
    });
    return response.data;
  },

  getStatistics: async (days: number = 30): Promise<Statistics> => {
    const response = await api.get('/stats', {
      params: { days }
    });
    return response.data;
  },

  // WebSocket
  createWebSocket: (scanId: string) => new WebSocketService(),
};

export default apiService;
