export type CameraStatus = "online" | "degraded" | "maintenance" | "offline";
export type PreviewAvailability = "available" | "degraded" | "unavailable" | "registry-only";

export interface CameraFixture {
  id: string;
  name: string;
  zone: string;
  type: string;
  ownership: string;
  status: CameraStatus;
  lastUpdated: string;
  coordinates: [number, number];
  previewAvailability: PreviewAvailability;
}

// Phase 1 fixtures are intentionally local metadata only. They model the UI
// contract without carrying a feed URL, session token, credential, or provider locator.
export const HCAM_CAMERA_FIXTURES: CameraFixture[] = [
  {
    id: "HCAM-AMD-001",
    name: "Riverfront Gate",
    zone: "Ahmedabad Central",
    type: "Fixed",
    ownership: "H-CAM Operations",
    status: "online",
    lastUpdated: "Just now",
    coordinates: [72.5813, 23.0314],
    previewAvailability: "available",
  },
  {
    id: "HCAM-AMD-002",
    name: "Transit Corridor North",
    zone: "Ahmedabad Central",
    type: "PTZ",
    ownership: "H-CAM Operations",
    status: "online",
    lastUpdated: "2 min ago",
    coordinates: [72.5706, 23.0448],
    previewAvailability: "available",
  },
  {
    id: "HCAM-GNR-011",
    name: "Civic District East",
    zone: "Gandhinagar",
    type: "Fixed",
    ownership: "H-CAM Operations",
    status: "degraded",
    lastUpdated: "6 min ago",
    coordinates: [72.6369, 23.2243],
    previewAvailability: "degraded",
  },
  {
    id: "HCAM-SRT-021",
    name: "South Approach",
    zone: "Surat",
    type: "Fixed",
    ownership: "H-CAM Operations",
    status: "online",
    lastUpdated: "1 min ago",
    coordinates: [72.8311, 21.1702],
    previewAvailability: "available",
  },
  {
    id: "HCAM-VDR-031",
    name: "Industrial Junction",
    zone: "Vadodara",
    type: "PTZ",
    ownership: "H-CAM Operations",
    status: "maintenance",
    lastUpdated: "18 min ago",
    coordinates: [73.1812, 22.3072],
    previewAvailability: "degraded",
  },
  {
    id: "HCAM-RJT-041",
    name: "West Sector Entry",
    zone: "Rajkot",
    type: "Fixed",
    ownership: "H-CAM Operations",
    status: "online",
    lastUpdated: "4 min ago",
    coordinates: [70.8022, 22.3039],
    previewAvailability: "unavailable",
  },
  {
    id: "HCAM-BHV-051",
    name: "Port Access Road",
    zone: "Bhavnagar",
    type: "Fixed",
    ownership: "H-CAM Operations",
    status: "offline",
    lastUpdated: "31 min ago",
    coordinates: [72.1362, 21.7645],
    previewAvailability: "unavailable",
  },
  {
    id: "HCAM-BHU-061",
    name: "North Gate",
    zone: "Bhuj",
    type: "Fixed",
    ownership: "H-CAM Operations",
    status: "online",
    lastUpdated: "3 min ago",
    coordinates: [69.6669, 23.2419],
    previewAvailability: "registry-only",
  },
];
