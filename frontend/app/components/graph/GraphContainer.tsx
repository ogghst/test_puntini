/**
 * GraphContainer component that handles API calls and state management for the Graph component.
 * 
 * Manages loading graph data from the backend API and provides it to the Graph component.
 * Now uses session-based API calls to ensure proper isolation and authentication.
 */

import React, { useEffect, useState } from 'react';
import { Graph } from './Graph';
import type { GraphData } from '../../models/graph';
import { useAuth } from '../auth/AuthContext';
import { SessionAPI, SessionAPIError, useGraphData } from '../../utils/session';

export interface GraphContainerProps {
  /** Optional class name */
  className?: string;
}

export function GraphContainer({ className }: GraphContainerProps) {
  const { token, user } = useAuth();
  const { graphData: apiGraphData, loading, error: apiError, loadGraphData } = useGraphData();
  const [sessionReady, setSessionReady] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);

  // Ensure session is ready when component mounts
  useEffect(() => {
    const ensureSession = async () => {
      if (!token || !user) {
        setError('Authentication required');
        return;
      }

      try {
        // Check if we have an active session
        const sessions = await SessionAPI.getMySessions();
        if (sessions.sessions.length === 0) {
          // Create a new session if none exists
          await SessionAPI.createSession({ user_id: user.username || 'user' });
        }
        setSessionReady(true);
      } catch (err) {
        console.error('Error ensuring session:', err);
        setError(err instanceof SessionAPIError ? err.message : 'Failed to create session');
      }
    };

    ensureSession();
  }, [token, user]);

  // Convert API graph data to component format
  const graphData: GraphData | undefined = apiGraphData ? {
    nodes: apiGraphData.nodes.map((node: any) => ({
      id: node.id,
      label: node.label,
      key: node.key,
      properties: node.properties || {},
      created_at: node.created_at,
      updated_at: node.updated_at,
    })),
    edges: apiGraphData.edges.map((edge: any) => ({
      id: edge.id,
      relationship_type: edge.relationship_type,
      source_id: edge.source_id,
      target_id: edge.target_id,
      source_key: edge.source_key,
      target_key: edge.target_key,
      source_label: edge.source_label,
      target_label: edge.target_label,
      properties: edge.properties || {},
      created_at: edge.created_at,
      updated_at: edge.updated_at,
    })),
  } : undefined;

  // Handle loading graph data
  const handleLoadGraph = async () => {
    if (!sessionReady) {
      setError('Session not ready. Please wait...');
      return;
    }

    setError(undefined);
    await loadGraphData();
  };

  // Determine error message
  const displayError = error || (apiError ? 
    (apiError.code === 404 ? 'No active sessions found. Please create a session first.' :
     apiError.code === 500 ? 'Graph store not available in session. Please try again.' :
     apiError.message) : undefined);

  return (
    <Graph
      data={graphData}
      loading={loading}
      error={displayError}
      onLoadGraph={handleLoadGraph}
      className={className}
    />
  );
}

export default GraphContainer;
