import React from 'react';
import { Box, Typography, Chip } from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

const ResultsPage: React.FC = () => {
  const navigate = useNavigate();
  
  const { data: results = [], isLoading } = useQuery(
    'scan-results',
    () => apiService.getResults({ limit: 100 }),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
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

  const columns: GridColDef[] = [
    {
      field: 'url',
      headerName: 'URL',
      flex: 1,
      minWidth: 300,
    },
    {
      field: 'timestamp',
      headerName: 'Scan Date',
      width: 180,
      valueFormatter: (params) => {
        return new Date(params.value).toLocaleString();
      },
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Chip
          label={params.value}
          size="small"
          color={params.value === 'completed' ? 'success' : params.value === 'failed' ? 'error' : 'default'}
        />
      ),
    },
    {
      field: 'tracker_count',
      headerName: 'Trackers',
      width: 100,
      type: 'number',
    },
    {
      field: 'privacy_score',
      headerName: 'Privacy Score',
      width: 120,
      type: 'number',
      renderCell: (params: GridRenderCellParams) => (
        <Box>
          {params.value ? `${params.value}/100` : 'N/A'}
        </Box>
      ),
    },
    {
      field: 'risk_level',
      headerName: 'Risk Level',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Chip
          label={params.value || 'unknown'}
          size="small"
          sx={{
            backgroundColor: getRiskColor(params.value || ''),
            color: 'white',
          }}
        />
      ),
    },
    {
      field: 'scan_duration',
      headerName: 'Duration',
      width: 120,
      valueFormatter: (params) => {
        return params.value ? `${params.value.toFixed(2)}s` : 'N/A';
      },
    },
  ];

  const handleRowClick = (params: any) => {
    navigate(`/scan/${params.row.scan_id}`);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Scan Results
      </Typography>
      
      <Box sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={results}
          columns={columns}
          getRowId={(row) => row.scan_id}
          loading={isLoading}
          onRowClick={handleRowClick}
          sx={{
            '& .MuiDataGrid-row:hover': {
              cursor: 'pointer',
            },
          }}
          initialState={{
            pagination: {
              paginationModel: { page: 0, pageSize: 25 },
            },
            sorting: {
              sortModel: [{ field: 'timestamp', sort: 'desc' }],
            },
          }}
          pageSizeOptions={[25, 50, 100]}
        />
      </Box>
    </Box>
  );
};

export default ResultsPage;
