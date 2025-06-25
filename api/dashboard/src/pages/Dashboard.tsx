import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  ResponsiveContainer,
} from 'recharts';
import { useQuery } from 'react-query';
import apiService from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const Dashboard: React.FC = () => {
  const { data: stats, isLoading, error } = useQuery(
    'statistics',
    () => apiService.getStatistics(30),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  const { data: recentResults } = useQuery(
    'recent-results',
    () => apiService.getResults({ limit: 5 }),
    {
      refetchInterval: 10000, // Refetch every 10 seconds
    }
  );

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <Typography color="error">
          Failed to load dashboard data
        </Typography>
      </Box>
    );
  }

  const riskData = stats ? Object.entries(stats.risk_distribution).map(([key, value]) => ({
    name: key,
    value,
  })) : [];

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low': return '#4caf50';
      case 'medium': return '#ff9800';
      case 'high': return '#f44336';
      case 'critical': return '#d32f2f';
      default: return '#757575';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                Total Scans
              </Typography>
              <Typography variant="h4">
                {stats?.total_scans || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                Trackers Found
              </Typography>
              <Typography variant="h4">
                {stats?.total_trackers_found || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                Avg Privacy Score
              </Typography>
              <Typography variant="h4">
                {stats?.avg_privacy_score?.toFixed(1) || '0.0'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                Risk Distribution
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {Object.entries(stats?.risk_distribution || {}).map(([level, count]) => (
                  <Chip
                    key={level}
                    label={`${level}: ${count}`}
                    size="small"
                    sx={{ backgroundColor: getRiskColor(level), color: 'white' }}
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Daily Scan Trend */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Daily Scan Trend (Last 30 Days)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats?.daily_scan_count || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#8884d8" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Risk Level Distribution */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Risk Level Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={riskData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {riskData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getRiskColor(entry.name)} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Most Common Trackers */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Most Common Trackers
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats?.most_common_trackers || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Scans */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Scans
              </Typography>
              <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                {recentResults?.map((result, index) => (
                  <Box
                    key={result.scan_id}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      py: 1,
                      px: 2,
                      backgroundColor: index % 2 === 0 ? 'grey.50' : 'transparent',
                      borderRadius: 1,
                      mb: 1,
                    }}
                  >
                    <Box>
                      <Typography variant="body2" noWrap>
                        {result.url}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {new Date(result.timestamp).toLocaleString()}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={`${result.tracker_count} trackers`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={result.risk_level || 'unknown'}
                        size="small"
                        sx={{
                          backgroundColor: getRiskColor(result.risk_level || ''),
                          color: 'white',
                        }}
                      />
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
