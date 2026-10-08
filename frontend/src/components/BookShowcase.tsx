import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * The landing page's three volumes, hosted from the authored Field Manuals document.
 *
 * The document is a complete page — its own stylesheet, renderer, media and lifecycle — so
 * it is loaded in an iframe rather than imported into this bundle. Nothing about the effect
 * is reconstructed here: `public/landing-pages/aquatrack-field-manuals.html` is derived
 * from the byte-exact authored source by `scripts/build-field-manuals.mjs`, which changes
 * copy and two `data-go` attributes and nothing else.
 *
 * Navigation is the only thing this component owns. Volumes I and II carry a route, and the
 * document posts it up rather than navigating itself; the messages are accepted only from
 * this frame, from this origin, and only for a route the app actually serves.
 */
const SOURCE = '/landing-pages/aquatrack-field-manuals.html';

/** The only routes a volume may open. Anything else in a message is ignored. */
const ROUTABLE = new Set(['/find', '/contribute']);

type OpenBookMessage = { type: 'aquatrack:open-book'; to: string };

function isOpenBookMessage(data: unknown): data is OpenBookMessage {
  if (typeof data !== 'object' || data === null) return false;
  const message = data as Record<string, unknown>;
  return message.type === 'aquatrack:open-book' && typeof message.to === 'string' && ROUTABLE.has(message.to);
}

export default function BookShowcase() {
  const frameRef = useRef<HTMLIFrameElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    function onMessage(event: MessageEvent) {
      // Same origin, same frame, known route — otherwise ignore it.
      if (event.origin !== window.location.origin) return;
      if (event.source !== frameRef.current?.contentWindow) return;
      if (!isOpenBookMessage(event.data)) return;
      navigate(event.data.to);
    }
    window.addEventListener('message', onMessage);
    return () => window.removeEventListener('message', onMessage);
  }, [navigate]);

  return (
    <iframe
      ref={frameRef}
      src={SOURCE}
      title="AquaTrack — Field Manuals of the Sea"
      className="book-showcase-frame"
      // Keeps the authored autoplaying cover loops and fullscreen behaviour; the document
      // is same-origin and self-contained, so it is deliberately not sandboxed.
      allow="autoplay; fullscreen"
    />
  );
}
