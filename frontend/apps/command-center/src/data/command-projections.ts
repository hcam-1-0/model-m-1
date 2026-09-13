import type { SituationSnapshot } from "@hcam/command-domain";
import type { GisFeatureSummary, GisLayerDefinition } from "@hcam/gis-contracts";
import {
  generatedGisFeatures,
  generatedLayers,
  generatedSituationSnapshot,
} from "@hcam/test-fixtures";

export const commandSnapshot = generatedSituationSnapshot(10) as SituationSnapshot;
export const commandFeatures = generatedGisFeatures(10) as readonly GisFeatureSummary[];
export const commandLayers = generatedLayers as readonly GisLayerDefinition[];
export const generatedClock = new Date("2026-09-08T00:20:00.000Z");
