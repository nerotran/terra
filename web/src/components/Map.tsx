import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import rewind from '@turf/rewind';
import type { Feature, Geometry } from 'geojson';
import type { Territory, BaseMap } from '../types';
import { getBaseMap } from '../api/client';

interface MapProps {
  territory: Territory | null;
}

export function Map({ territory }: MapProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [baseMap, setBaseMap] = useState<BaseMap | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Load base map data once from API
  useEffect(() => {
    getBaseMap('land')
      .then(setBaseMap)
      .catch((err) => console.error('Failed to load base map:', err));
  }, []);

  // Track container size changes
  useEffect(() => {
    if (!svgRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDimensions({ width, height });
    });

    resizeObserver.observe(svgRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  useEffect(() => {
    if (!svgRef.current || dimensions.width === 0) return;

    const svg = d3.select(svgRef.current);
    const { width, height } = dimensions;

    // Clear previous
    svg.selectAll('*').remove();

    // Projection centered on Mediterranean
    const projection = d3.geoMercator()
      .center([15, 42])
      .scale(width / 2)
      .translate([width / 2, height / 2]);

    const path = d3.geoPath().projection(projection);

    // Draw base map land features
    if (baseMap?.features) {
      baseMap.features.forEach((feature) => {
        if (!feature.geometry) return;

        const geoFeature: Feature<Geometry> = {
          type: 'Feature',
          properties: {},
          geometry: feature.geometry as Geometry
        };
        const rewound = rewind(geoFeature, { reverse: true });

        svg.append('path')
          .datum(rewound)
          .attr('d', path)
          .attr('fill', '#e8e8e8')
          .attr('stroke', '#ccc')
          .attr('stroke-width', 0.3);
      });
    }

    // Draw territory if available
    if (territory?.geometry) {
      const feature: Feature<Geometry> = {
        type: 'Feature',
        properties: {},
        geometry: territory.geometry as Geometry
      };
      const rewound = rewind(feature, { reverse: true });

      svg.append('path')
        .datum(rewound)
        .attr('d', path)
        .attr('fill', territory.color ?? '#8B0000')
        .attr('stroke', '#fff')
        .attr('stroke-width', 0.5);
    }

  }, [territory, baseMap, dimensions]);

  return (
    <svg
      ref={svgRef}
      style={{ width: '100%', height: '100%', background: '#b3d1ff' }}
    />
  );
}
