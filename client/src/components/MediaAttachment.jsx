function getMediaBaseUrl() {
  const configuredBase = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api";
  return configuredBase.replace(/\/api\/?$/, "");
}

function resolveMediaUrl(inputUrl) {
  const normalized = String(inputUrl || "").trim();

  if (!normalized) {
    return "";
  }

  const token = localStorage.getItem("token");

  if (normalized.startsWith("/api/")) {
    const baseUrl = `${getMediaBaseUrl()}${normalized}`;
    return token ? `${baseUrl}?token=${encodeURIComponent(token)}` : baseUrl;
  }

  return normalized;
}

function getYouTubeEmbedUrl(inputUrl) {
  const normalized = String(inputUrl || "").trim();

  if (!normalized) {
    return null;
  }

  if (normalized.startsWith("/")) {
    return null;
  }

  try {
    const parsed = new URL(normalized);
    const host = parsed.hostname.replace(/^www\./i, "").toLowerCase();

    if (host === "youtu.be") {
      const id = parsed.pathname.slice(1);
      return id ? `https://www.youtube.com/embed/${id}` : null;
    }

    if (host === "youtube.com" || host === "m.youtube.com") {
      const watchId = parsed.searchParams.get("v");
      if (watchId) {
        return `https://www.youtube.com/embed/${watchId}`;
      }

      const pathParts = parsed.pathname.split("/").filter(Boolean);
      if (pathParts[0] === "shorts" && pathParts[1]) {
        return `https://www.youtube.com/embed/${pathParts[1]}`;
      }

      if (pathParts[0] === "embed" && pathParts[1]) {
        return `https://www.youtube.com/embed/${pathParts[1]}`;
      }
    }
  } catch {
    return null;
  }

  return null;
}

function detectMediaType(url) {
  const normalized = String(url || "").trim();
  const resolvedUrl = resolveMediaUrl(normalized);

  if (!resolvedUrl) {
    return { type: "none" };
  }

  const isRelativePath = normalized.startsWith("/");
  const imagePattern = /\.(png|jpe?g|gif|webp|svg)(\?.*)?$/i;
  const videoPattern = /\.(mp4|webm|ogg|mov)(\?.*)?$/i;

  const youtubeEmbedUrl = getYouTubeEmbedUrl(normalized);
  if (youtubeEmbedUrl) {
    return { type: "youtube", embedUrl: youtubeEmbedUrl, url: normalized };
  }

  if (isRelativePath && imagePattern.test(normalized)) {
    return { type: "image", url: resolvedUrl };
  }

  if (isRelativePath && videoPattern.test(normalized)) {
    return { type: "video", url: resolvedUrl };
  }

  if (imagePattern.test(normalized)) {
    return { type: "image", url: resolvedUrl };
  }

  if (videoPattern.test(normalized)) {
    return { type: "video", url: resolvedUrl };
  }

  return { type: "link", url: resolvedUrl };
}

function MediaAttachment({ url }) {
  const media = detectMediaType(url);

  if (media.type === "none") {
    return null;
  }

  return (
    <div className="media-attachment">
      {media.type === "image" && (
        <img
          className="media-preview"
          src={media.url}
          alt="Project media attachment"
          loading="lazy"
        />
      )}

      {media.type === "video" && (
        <video className="media-preview" controls preload="metadata">
          <source src={media.url} />
          Your browser does not support embedded video playback.
        </video>
      )}

      {media.type === "youtube" && (
        <iframe
          className="media-preview media-preview-embed"
          src={media.embedUrl}
          title="Project media video"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
        />
      )}

    </div>
  );
}

export default MediaAttachment;
