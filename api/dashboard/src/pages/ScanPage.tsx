import React from 'react';
import { Box, Typography, Button, TextField, Grid, LinearProgress, FormControlLabel, Checkbox } from '@mui/material';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';
import apiService, { ScanRequest } from '../services/api';

const ScanPage: React.FC = () => {
  const [url, setUrl] = React.useState('');
  const [scanType, setScanType] = React.useState<'basic' | 'enhanced'>('basic');
  const [enableJavascript, setEnableJavascript] = React.useState(false);
  const [enableMlAnalysis, setEnableMlAnalysis] = React.useState(false);
  const [enableAdvancedFingerprinting, setEnableAdvancedFingerprinting] = React.useState(false);

  const navigate = useNavigate();
  const scanMutation = useMutation<unknown, unknown, ScanRequest>(scanData => apiService.createScan(scanData), {
    onSuccess: (data: any) => {
      navigate(`/scan/${data.scan_id}`);
    },
  });

  const handleScan = () => {
    scanMutation.mutate({
      url,
      scan_type: scanType,
      enable_javascript: enableJavascript,
      enable_ml_analysis: enableMlAnalysis,
      enable_advanced_fingerprinting: enableAdvancedFingerprinting,
    });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        New Scan
      </Typography>
      <Box maxWidth="md" sx={{ my: 4 }}>
        <TextField
          fullWidth
          label="URL"
          value={url}
          onChange={e => setUrl(e.target.value)}
          variant="outlined"
          sx={{ mb: 3 }}
        />
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={4}>
            <FormControlLabel
              control={<Checkbox checked={scanType === 'enhanced'} onChange={() => setScanType(scanType === 'basic' ? 'enhanced' : 'basic')} />}
              label="Enhanced Scan"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormControlLabel
              control={<Checkbox checked={enableJavascript} onChange={() => setEnableJavascript(!enableJavascript)} />}
              label="Enable JavaScript"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormControlLabel
              control={<Checkbox checked={enableMlAnalysis} onChange={() => setEnableMlAnalysis(!enableMlAnalysis)} />}
              label="Enable ML Analysis"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormControlLabel
              control={<Checkbox checked={enableAdvancedFingerprinting} onChange={() => setEnableAdvancedFingerprinting(!enableAdvancedFingerprinting)} />}
              label="Enable Advanced Fingerprinting"
            />
          </Grid>
        </Grid>
        <Button variant="contained" color="primary" onClick={handleScan} disabled={scanMutation.isLoading}>
          Start Scan
        </Button>
      </Box>
      {scanMutation.isLoading && <LinearProgress />}
    </Box>
  );
};

export default ScanPage;

