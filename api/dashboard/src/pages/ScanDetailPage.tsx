import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
} from '@mui/material';
import { useQuery } from 'react-query';
import apiService, { WebSocketService } from '../services/api';

interface ProgressUpdate {
  scan_id: string;
  status: string;
  progress: number;
  message: string;
  result?: any;
  error?: string;
}

const ScanDetailPage: React.FC = () => {
  const { scanId } = useParams<{ scanId: string }>();
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [wsService, setWsService] = useState<WebSocketService | null>(null);

  const { data: scanResult, refetch } = useQuery(
    ['scan-result', scanId],
    () => apiService.getScanResult(scanId!),
    {
      enabled: !!scanId,
      refetchInterval: (data) => {
        // Stop refetching if scan is completed or failed
        return data?.status === 'completed' || data?.status === 'failed' ? false : 5000;
      },
    }
  );

  useEffect(() => {
    if (!scanId) return;

    const ws = new WebSocketService();
    setWsService(ws);

    ws.connect(scanId)
      .then(() => {
        ws.onMessage('progress', (data: ProgressUpdate) => {
          setProgress(data);
          if (data.status === 'completed' || data.status === 'failed') {
            refetch();
          }
        });
      })
      .catch((error) => {
        console.error('WebSocket connection failed:', error);
      });

    return () => {
      ws.disconnect();
    };
  }, [scanId, refetch]);

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low': return '#4caf50';
      case 'medium': return '#ff9800';
      case 'high': return '#f44336';
      case 'critical': return '#d32f2f';
      default: return '#757575';
    }
  };

  const isScanning = scanResult?.status === 'scanning' || scanResult?.status === 'pending';
  const currentProgress = progress?.progress || 0;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Scan Details
      </Typography>

      {scanResult && (
        <Grid container spacing={3}>
          {/* Scan Overview */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Scan Overview
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography><strong>URL:</strong> {scanResult.url}</Typography>
                    <Typography><strong>Status:</strong> {scanResult.status}</Typography>
                    <Typography><strong>Started:</strong> {new Date(scanResult.timestamp).toLocaleString()}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography><strong>Scan ID:</strong> {scanResult.scan_id}</Typography>
                    <Typography><strong>Trackers Found:</strong> {scanResult.tracker_count}</Typography>
                    {scanResult.privacy_score && (
                      <Typography><strong>Privacy Score:</strong> {scanResult.privacy_score}/100</Typography>
                    )}
                  </Grid>
                </Grid>

                {isScanning && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" gutterBottom>
                      {progress?.message || 'Scanning in progress...'}
                    </Typography>
                    <LinearProgress variant="determinate" value={currentProgress} />
                    <Typography variant="caption" sx={{ mt: 1 }}>
                      {currentProgress}% complete
                    </Typography>
                  </Box>
                )}

                {scanResult.error && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    {scanResult.error}
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Privacy Analysis */}
          {scanResult.privacy_analysis && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Privacy Analysis
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {scanResult.privacy_score && (
                      <Box>
                        <Typography variant="body2">Privacy Score</Typography>
                        <Typography variant="h4">{scanResult.privacy_score}/100</Typography>
                      </Box>
                    )}
                    {scanResult.risk_level && (
                      <Chip
                        label={`Risk Level: ${scanResult.risk_level}`}
                        sx={{
                          backgroundColor: getRiskColor(scanResult.risk_level),
                          color: 'white',
                          alignSelf: 'flex-start'
                        }}
                      />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Performance Metrics */}
          {scanResult.performance_metrics && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Metrics
                  </Typography>
                  <Typography>
                    <strong>Response Time:</strong> {scanResult.performance_metrics.response_time}ms
                  </Typography>
                  <Typography>
                    <strong>Content Size:</strong> {scanResult.performance_metrics.content_length} bytes
                  </Typography>
                  <Typography>
                    <strong>Status Code:</strong> {scanResult.performance_metrics.status_code}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Detected Trackers */}
          {scanResult.trackers && scanResult.trackers.length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Detected Trackers ({scanResult.trackers.length})
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Name</TableCell>
                          <TableCell>Category</TableCell>
                          <TableCell>Risk Level</TableCell>
                          <TableCell>Domain</TableCell>
                          <TableCell>Purpose</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {scanResult.trackers.map((tracker, index) => (
                          <TableRow key={index}>
                            <TableCell>{tracker.tracker_type || tracker.name}</TableCell>
                            <TableCell>{tracker.category}</TableCell>
                            <TableCell>
                              <Chip
                                label={tracker.risk_level}
                                size="small"
                                sx={{
                                  backgroundColor: getRiskColor(tracker.risk_level),
                                  color: 'white',
                                }}
                              />
                            </TableCell>
                            <TableCell>{tracker.domain}</TableCell>
                            <TableCell>{tracker.purpose || 'N/A'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}
    </Box>
  );
};

export default ScanDetailPage;
