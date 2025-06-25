import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  AreaChart,
  Area,
} from 'recharts';
import { useQuery } from 'react-query';
import apiService from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d', '#ffc658'];

const StatsPage: React.FC = () => {
  const [timeRange, setTimeRange] = React.useState(30);

  const { data: stats, isLoading } = useQuery(
    ['statistics', timeRange],
    () => apiService.getStatistics(timeRange),
    {
      refetchInterval: 60000, // Refetch every minute
    }
  );

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low': return '#4caf50';
      case 'medium': return '#ff9800';
      case 'high': return '#f44336';
      case 'critical': return '#d32f2f';
      default: return '#757575';
    }
  };

  const riskData = stats ? Object.entries(stats.risk_distribution).map(([key, value]) => ({
    name: key,
    value,
    color: getRiskColor(key),
  })) : [];

  // Generate sample data for domain heatmap
  const domainHeatmapData = [
    { domain: 'google-analytics.com', visits: 245, risk: 'low' },
    { domain: 'facebook.com', visits: 187, risk: 'medium' },
    { domain: 'doubleclick.net', visits: 156, risk: 'high' },
    { domain: 'googletagmanager.com', visits: 134, risk: 'low' },
    { domain: 'amazon-adsystem.com', visits: 98, risk: 'medium' },
    { domain: 'scorecardresearch.com', visits: 76, risk: 'high' },
    { domain: 'twitter.com', visits: 65, risk: 'low' },
    { domain: 'adsystem.com', visits: 54, risk: 'critical' },
  ];

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Statistics & Analytics
        </Typography>
        <Typography>Loading statistics...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Statistics & Analytics
        </Typography>
        <FormControl sx={{ minWidth: 120 }}>
          <InputLabel>Time Range</InputLabel>
          <Select
            value={timeRange}
            label="Time Range"
            onChange={(e) => setTimeRange(Number(e.target.value))}
          >
            <MenuItem value={7}>7 Days</MenuItem>
            <MenuItem value={30}>30 Days</MenuItem>
            <MenuItem value={90}>90 Days</MenuItem>
            <MenuItem value={365}>1 Year</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Grid container spacing={3}>
        {/* Tracker Trends */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Daily Scan & Tracker Trends
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={stats?.daily_scan_count || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stackId="1"
                    stroke="#8884d8"
                    fill="#8884d8"
                    name="Scans"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Risk Distribution */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Risk Level Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={riskData}
                    cx="50%"
                    cy="50%"
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {riskData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Trackers */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Most Common Trackers
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={stats?.most_common_trackers || []}
                  layout="horizontal"
                  margin={{ left: 100 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={100} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Domain Heatmap */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Domain Activity Heatmap
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <ScatterChart data={domainHeatmapData}>
                  <CartesianGrid />
                  <XAxis dataKey="visits" type="number" name="visits" />
                  <YAxis dataKey="domain" type="category" />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter
                    dataKey="visits"
                    fill="#8884d8"
                    shape={(props: any) => {
                      const { cx, cy, payload } = props;
                      const size = Math.max(4, payload.visits / 10);
                      return (
                        <circle
                          cx={cx}
                          cy={cy}
                          r={size}
                          fill={getRiskColor(payload.risk)}
                        />
                      );
                    }}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Privacy Score Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Privacy Score Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={[
                    { range: '0-20', count: 12, color: '#d32f2f' },
                    { range: '21-40', count: 28, color: '#f44336' },
                    { range: '41-60', count: 45, color: '#ff9800' },
                    { range: '61-80', count: 67, color: '#4caf50' },
                    { range: '81-100', count: 34, color: '#2e7d32' },
                  ]}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Scan Performance */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Scan Performance Metrics
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={stats?.daily_scan_count?.slice(-14) || []}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#8884d8"
                    name="Daily Scans"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Summary Stats */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Summary Statistics (Last {timeRange} Days)
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h3" color="primary">
                      {stats?.total_scans || 0}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Total Scans
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h3" color="secondary">
                      {stats?.total_trackers_found || 0}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Trackers Found
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h3" color="success.main">
                      {stats?.avg_privacy_score?.toFixed(1) || '0.0'}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Avg Privacy Score
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h3" color="warning.main">
                      {domainHeatmapData.length}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Unique Domains
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default StatsPage;
