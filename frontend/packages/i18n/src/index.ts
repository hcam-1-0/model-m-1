import { createElement, type ReactNode } from "react";
import { IntlProvider } from "react-intl";
import type { DisplayPreferences } from "@hcam/contracts";

export const locales = ["en", "gu", "hi", "en-XA"] as const;
export type Locale = (typeof locales)[number];
export const baseMessages = {
  "app.name": "NETRA SENTINEL",
  "shell.generated": "Generated environment. No operational data.",
  "shell.skip": "Skip to main content",
  "shell.navigation": "Primary navigation",
  "shell.portals": "Portal switcher",
  "shell.command": "Open command search",
  "shell.session": "Session menu",
  "shell.department": "Department",
  "shell.locale": "Language",
  "shell.theme": "Change theme",
  "shell.menu": "Open navigation",
  "shell.close": "Close",
  "shell.profile": "Resource profile",
  "portal.command": "Command Center",
  "portal.gis": "GIS Center",
  "portal.operations": "Operations Center",
  "portal.intelligence": "Intelligence Center",
  "portal.investigations": "Investigation Center",
  "portal.evidence": "Evidence Center",
  "portal.admin": "Admin Center",
  "portal.security": "Security Center",
  "workspace.overview": "Operational overview",
  "workspace.activity": "Recent generated activity",
  "workspace.health": "Platform health",
  "workspace.freshness": "Updated moments ago",
  "workspace.review": "Items requiring review",
  "workspace.open": "Open items",
  "workspace.coverage": "Available sources",
  "workspace.ready": "Foundation ready",
  "workspace.noActions": "No operational actions are enabled in this foundation build.",
  "state.loading": "Loading authorized workspace",
  "state.empty": "No items in this generated view",
  "state.ready": "Workspace is current",
  "state.partial": "Some generated results are incomplete",
  "state.stale": "Displayed information may be stale",
  "state.degraded": "Optional visual features are unavailable",
  "state.denied": "Access is not available for this route",
  "state.conflict": "The server state changed; refresh is required",
  "state.failure": "The request could not be completed safely",
  "state.recovery": "Refreshing authoritative state",
  "state.correction": "A correction has changed this view",
  "state.unknown": "Authoritative state is unknown",
  "state.retracted": "This record has been retracted",
  "state.unsupported": "This capability is not supported",
  "state.success": "The server confirmed the request",
  "action.refresh": "Refresh",
  "action.viewAll": "View all",
  "camera.catalogue": "Camera catalogue",
  "camera.detail": "Camera detail",
  "camera.diagnostics": "Stream diagnostics",
  "camera.live": "Live workspace",
  "camera.wall": "Monitor wall",
  "camera.workspaces": "Workspaces",
  "camera.generatedSession": "Generated live session",
  "camera.viewOnly": "View-only controls",
  "investigation.overview": "Investigation overview",
  "investigation.timeline": "Investigation timeline",
  "investigation.reconstruction": "Exact-revision reconstruction",
  "investigation.corrections": "Corrections and retractions",
  "evidence.overview": "Evidence reference overview",
  "evidence.integrity": "Integrity history",
  "evidence.provenance": "Provenance and custody",
  "evidence.policy": "Non-operative policy previews",
  "administration.overview": "Administration overview",
  "security.assurance": "Security assurance",
  "operations.platform": "Platform operations",
  "control.nonEffective": "Generated preview; no operational effect",
} as const;
export type MessageId = keyof typeof baseMessages;

const gu: Record<MessageId, string> = {
  ...baseMessages,
  "shell.generated": "બનાવટી પર્યાવરણ. કોઈ કાર્યરત માહિતી નથી.",
  "shell.skip": "મુખ્ય સામગ્રી પર જાઓ",
  "shell.navigation": "મુખ્ય નેવિગેશન",
  "shell.department": "વિભાગ",
  "shell.locale": "ભાષા",
  "portal.command": "કમાન્ડ સેન્ટર",
  "portal.gis": "જીઆઇએસ સેન્ટર",
  "portal.operations": "ઓપરેશન્સ સેન્ટર",
  "portal.intelligence": "ઇન્ટેલિજન્સ સેન્ટર",
  "portal.investigations": "તપાસ સેન્ટર",
  "portal.evidence": "પુરાવા સેન્ટર",
  "portal.admin": "એડમિન સેન્ટર",
  "portal.security": "સુરક્ષા સેન્ટર",
  "workspace.overview": "કાર્યકારી અવલોકન",
  "workspace.activity": "તાજેતરની બનાવટી પ્રવૃત્તિ",
  "workspace.health": "પ્લેટફોર્મ સ્થિતિ",
  "workspace.freshness": "થોડી ક્ષણ પહેલાં અપડેટ થયું",
  "workspace.review": "સમીક્ષા જરૂરી વસ્તુઓ",
  "workspace.open": "ખુલ્લી વસ્તુઓ",
  "workspace.coverage": "ઉપલબ્ધ સ્ત્રોતો",
  "workspace.ready": "આધાર તૈયાર છે",
  "workspace.noActions": "આ ફાઉન્ડેશન બિલ્ડમાં કોઈ કાર્યરત ક્રિયા સક્રિય નથી.",
  "state.loading": "અધિકૃત કાર્યસ્થળ લોડ થઈ રહ્યું છે",
  "state.empty": "આ બનાવટી દૃશ્યમાં કોઈ વસ્તુ નથી",
  "state.ready": "કાર્યસ્થળ વર્તમાન છે",
  "state.partial": "કેટલાક બનાવટી પરિણામો અધૂરા છે",
  "state.stale": "દર્શાવેલી માહિતી જૂની હોઈ શકે છે",
  "state.degraded": "વૈકલ્પિક દૃશ્ય સુવિધાઓ ઉપલબ્ધ નથી",
  "state.denied": "આ માર્ગ માટે પ્રવેશ ઉપલબ્ધ નથી",
  "state.conflict": "સર્વર સ્થિતિ બદલાઈ છે; રિફ્રેશ જરૂરી છે",
  "state.failure": "વિનંતી સુરક્ષિત રીતે પૂર્ણ થઈ શકી નથી",
  "state.recovery": "અધિકૃત સ્થિતિ રિફ્રેશ થઈ રહી છે",
  "state.correction": "સુધારાથી આ દૃશ્ય બદલાયું છે",
  "state.unknown": "અધિકૃત સ્થિતિ અજ્ઞાત છે",
  "state.retracted": "આ રેકોર્ડ પાછો ખેંચાયો છે",
  "state.unsupported": "આ ક્ષમતા સમર્થિત નથી",
  "state.success": "સર્વરે વિનંતીની પુષ્ટિ કરી",
  "action.refresh": "રિફ્રેશ",
  "action.viewAll": "બધું જુઓ",
  "camera.catalogue": "કેમેરા સૂચિ",
  "camera.detail": "કેમેરા વિગત",
  "camera.diagnostics": "સ્ટ્રીમ નિદાન",
  "camera.live": "લાઇવ કાર્યસ્થળ",
  "camera.wall": "મોનિટર વોલ",
  "camera.workspaces": "કાર્યસ્થળો",
  "camera.generatedSession": "બનાવટી લાઇવ સત્ર",
  "camera.viewOnly": "માત્ર જોવાના નિયંત્રણો",
  "administration.overview": "વહીવટી અવલોકન",
  "security.assurance": "સુરક્ષા ખાતરી",
  "operations.platform": "પ્લેટફોર્મ કામગીરી",
  "control.nonEffective": "બનાવટી પૂર્વદર્શન; કોઈ કાર્યરત અસર નથી",
};
const hi: Record<MessageId, string> = {
  ...baseMessages,
  "shell.generated": "निर्मित वातावरण। कोई परिचालन डेटा नहीं।",
  "shell.skip": "मुख्य सामग्री पर जाएं",
  "shell.navigation": "मुख्य नेविगेशन",
  "shell.department": "विभाग",
  "shell.locale": "भाषा",
  "portal.command": "कमांड सेंटर",
  "portal.gis": "जीआईएस सेंटर",
  "portal.operations": "ऑपरेशंस सेंटर",
  "portal.intelligence": "इंटेलिजेंस सेंटर",
  "portal.investigations": "जांच सेंटर",
  "portal.evidence": "साक्ष्य सेंटर",
  "portal.admin": "एडमिन सेंटर",
  "portal.security": "सुरक्षा सेंटर",
  "workspace.overview": "परिचालन अवलोकन",
  "workspace.activity": "हाल की निर्मित गतिविधि",
  "workspace.health": "प्लेटफॉर्म स्थिति",
  "workspace.freshness": "कुछ क्षण पहले अपडेट किया गया",
  "workspace.review": "समीक्षा आवश्यक आइटम",
  "workspace.open": "खुले आइटम",
  "workspace.coverage": "उपलब्ध स्रोत",
  "workspace.ready": "आधार तैयार है",
  "workspace.noActions": "इस फाउंडेशन बिल्ड में कोई परिचालन कार्रवाई सक्षम नहीं है।",
  "state.loading": "अधिकृत कार्यक्षेत्र लोड हो रहा है",
  "state.empty": "इस निर्मित दृश्य में कोई आइटम नहीं",
  "state.ready": "कार्यक्षेत्र वर्तमान है",
  "state.partial": "कुछ निर्मित परिणाम अधूरे हैं",
  "state.stale": "दिखाई गई जानकारी पुरानी हो सकती है",
  "state.degraded": "वैकल्पिक दृश्य सुविधाएं उपलब्ध नहीं हैं",
  "state.denied": "इस मार्ग के लिए प्रवेश उपलब्ध नहीं है",
  "state.conflict": "सर्वर स्थिति बदल गई; रीफ्रेश आवश्यक है",
  "state.failure": "अनुरोध सुरक्षित रूप से पूरा नहीं हो सका",
  "state.recovery": "प्रामाणिक स्थिति रीफ्रेश हो रही है",
  "state.correction": "सुधार ने इस दृश्य को बदल दिया है",
  "state.unknown": "आधिकारिक स्थिति अज्ञात है",
  "state.retracted": "यह रिकॉर्ड वापस लिया गया है",
  "state.unsupported": "यह क्षमता समर्थित नहीं है",
  "state.success": "सर्वर ने अनुरोध की पुष्टि की",
  "action.refresh": "रीफ्रेश",
  "action.viewAll": "सभी देखें",
  "camera.catalogue": "कैमरा सूची",
  "camera.detail": "कैमरा विवरण",
  "camera.diagnostics": "स्ट्रीम निदान",
  "camera.live": "लाइव कार्यक्षेत्र",
  "camera.wall": "मॉनिटर वॉल",
  "camera.workspaces": "कार्यक्षेत्र",
  "camera.generatedSession": "निर्मित लाइव सत्र",
  "camera.viewOnly": "केवल देखने के नियंत्रण",
  "administration.overview": "प्रशासन अवलोकन",
  "security.assurance": "सुरक्षा आश्वासन",
  "operations.platform": "प्लेटफॉर्म संचालन",
  "control.nonEffective": "निर्मित पूर्वावलोकन; कोई परिचालन प्रभाव नहीं",
};
const pseudo = Object.fromEntries(
  Object.entries(baseMessages).map(([key, value]) => [
    key,
    `[!! ${value.replace(/[aeiou]/gi, "$&$&")} !!]`,
  ]),
) as Record<MessageId, string>;
export const catalogues: Record<Locale, Record<MessageId, string>> = {
  en: baseMessages,
  gu,
  hi,
  "en-XA": pseudo,
};
export function hasCompleteCatalogue(locale: Locale): boolean {
  return Object.keys(baseMessages).every((key) => key in catalogues[locale]);
}
export function HcamIntlProvider({
  locale,
  children,
}: {
  readonly locale: Locale;
  readonly children: ReactNode;
}): ReactNode {
  return createElement(
    IntlProvider,
    { locale, defaultLocale: "en", messages: catalogues[locale], onError: () => undefined },
    children,
  );
}

export function parseDisplayPreferences(
  value: unknown,
  now = new Date(),
): DisplayPreferences | null {
  if (!value || typeof value !== "object") return null;
  const item = value as Record<string, unknown>;
  if (
    item.version !== 1 ||
    !["light", "dark", "system"].includes(String(item.theme)) ||
    !["compact", "comfortable", "spacious"].includes(String(item.density)) ||
    !["en", "gu", "hi"].includes(String(item.locale)) ||
    typeof item.reducedMotion !== "boolean" ||
    typeof item.expiresAt !== "string" ||
    Date.parse(item.expiresAt) <= now.getTime()
  )
    return null;
  return item as unknown as DisplayPreferences;
}
export function saveDisplayPreferences(
  storage: Pick<Storage, "setItem">,
  preference: DisplayPreferences,
): void {
  storage.setItem("hcam.display.v1", JSON.stringify(preference));
}
export function loadDisplayPreferences(
  storage: Pick<Storage, "getItem" | "removeItem">,
  now = new Date(),
): DisplayPreferences | null {
  const raw = storage.getItem("hcam.display.v1");
  if (!raw || raw.length > 2048) {
    if (raw) storage.removeItem("hcam.display.v1");
    return null;
  }
  try {
    const parsed = parseDisplayPreferences(JSON.parse(raw), now);
    if (!parsed) storage.removeItem("hcam.display.v1");
    return parsed;
  } catch {
    storage.removeItem("hcam.display.v1");
    return null;
  }
}
