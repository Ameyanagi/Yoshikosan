# Camera Black Screen Issue on iPhone - Analysis & Fix

## Problem

Camera appears blacked out on iPhone when using the Capture Current Work feature in work sessions.

## Root Cause Analysis

### Current Implementation Issues

**File**: `yoshikosan-frontend/components/camera-capture.tsx:29-34`

```typescript
const mediaStream = await navigator.mediaDevices.getUserMedia({
  video: { facingMode: "environment" },  // ❌ PROBLEM: Too restrictive
  audio: false,
});
```

### iPhone-Specific Issues

1. **facingMode Constraint Too Strict**:
   - iOS Safari requires exact constraint matching
   - If device doesn't have rear camera accessible, stream fails silently
   - Results in black screen instead of error

2. **Missing playsinline Attribute**:
   - iOS requires `playsinline` for inline video playback
   - Without it, video may not render properly
   - ✅ Already present in code: `<video ref={videoRef} autoPlay playsInline />`

3. **Video Dimensions Not Set**:
   - iOS may not initialize video without explicit dimensions
   - Black screen occurs when video stream exists but doesn't render

4. **Missing Video Ready Check**:
   - Code attempts to capture before video is ready
   - `videoWidth` and `videoHeight` may be 0

## Recommended Fixes

### Fix 1: Use Ideal Constraints Instead of Exact

**Priority**: HIGH
**Impact**: Resolves black screen on most devices

```typescript
// BEFORE (current - too restrictive)
const mediaStream = await navigator.mediaDevices.getUserMedia({
  video: { facingMode: "environment" },
  audio: false,
});

// AFTER (recommended - flexible fallback)
const mediaStream = await navigator.mediaDevices.getUserMedia({
  video: {
    facingMode: { ideal: "environment" },  // ✅ Prefer rear, fallback to front
    width: { ideal: 1920, max: 1920 },
    height: { ideal: 1080, max: 1080 }
  },
  audio: false,
});
```

**Why this works**:
- `ideal` allows fallback to front camera if rear unavailable
- Explicit dimensions help iOS initialize video properly
- Max constraints prevent excessive resolution

### Fix 2: Wait for Video Ready Before Enabling Capture

**Priority**: HIGH
**Impact**: Prevents capturing black/empty frames

```typescript
// AFTER setting srcObject, add loadedmetadata listener
const startCamera = async () => {
  try {
    setError(null);
    const mediaStream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: "environment" },
        width: { ideal: 1920, max: 1920 },
        height: { ideal: 1080, max: 1080 }
      },
      audio: false,
    });

    if (videoRef.current) {
      videoRef.current.srcObject = mediaStream;

      // ✅ Wait for video to be ready
      await new Promise<void>((resolve) => {
        videoRef.current!.onloadedmetadata = () => {
          videoRef.current!.play();
          resolve();
        };
      });
    }

    setStream(mediaStream);
    setIsActive(true);
  } catch (err) {
    setError(err instanceof Error ? err.message : "Failed to access camera");
  }
};
```

### Fix 3: Add Video Dimension Validation Before Capture

**Priority**: MEDIUM
**Impact**: Better error handling, prevents invalid captures

```typescript
const captureImage = () => {
  if (!videoRef.current || !canvasRef.current) return;

  const video = videoRef.current;
  const canvas = canvasRef.current;

  // ✅ Validate video is ready
  if (video.videoWidth === 0 || video.videoHeight === 0) {
    setError("Camera not ready. Please try again.");
    return;
  }

  const context = canvas.getContext("2d");
  if (!context) return;

  // Set canvas size to match video
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  // Draw current video frame to canvas
  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  // Convert to base64 (remove data:image/jpeg;base64, prefix)
  const imageBase64 = canvas.toDataURL("image/jpeg", 0.9).split(",")[1];

  onCapture(imageBase64);
  stopCamera();
};
```

### Fix 4: Add CSS for Better Video Rendering

**Priority**: LOW
**Impact**: Ensures video fills container properly

```typescript
// In the video element
<video
  ref={videoRef}
  autoPlay
  playsInline
  muted  // ✅ Add muted for iOS autoplay
  className="w-full object-cover"  // ✅ object-cover ensures proper aspect
  style={{ minHeight: '300px' }}  // ✅ Minimum height prevents collapse
/>
```

## Complete Fixed Implementation

```typescript
"use client";

import { useRef, useState, useEffect } from "react";

interface CameraCaptureProps {
  onCapture: (imageBase64: string) => void;
  disabled?: boolean;
}

export function CameraCapture({ onCapture, disabled }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      // Cleanup: stop stream when component unmounts
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [stream]);

  const startCamera = async () => {
    try {
      setError(null);

      // ✅ FIX 1: Use ideal constraints for better compatibility
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },  // Prefer rear, fallback to front
          width: { ideal: 1920, max: 1920 },
          height: { ideal: 1080, max: 1080 }
        },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;

        // ✅ FIX 2: Wait for video metadata to load
        await new Promise<void>((resolve) => {
          videoRef.current!.onloadedmetadata = () => {
            videoRef.current!.play().catch(err => {
              console.error("Failed to play video:", err);
            });
            resolve();
          };
        });
      }

      setStream(mediaStream);
      setIsActive(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to access camera";
      setError(errorMessage);
      console.error("Camera error:", err);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsActive(false);
  };

  const captureImage = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    // ✅ FIX 3: Validate video dimensions before capture
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      setError("カメラの準備ができていません。もう一度お試しください。");
      return;
    }

    const context = canvas.getContext("2d");
    if (!context) return;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to base64 with quality optimization
    const imageBase64 = canvas.toDataURL("image/jpeg", 0.85).split(",")[1];

    onCapture(imageBase64);
    stopCamera();
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {!isActive ? (
        <button
          onClick={startCamera}
          disabled={disabled}
          className="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
        >
          📷 カメラを起動
        </button>
      ) : (
        <>
          <div className="relative overflow-hidden rounded-lg bg-black">
            {/* ✅ FIX 4: Better video styling for iOS */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full object-cover"
              style={{ minHeight: '300px' }}
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={captureImage}
              className="flex-1 rounded-lg bg-green-600 px-4 py-3 font-medium text-white hover:bg-green-700"
            >
              📸 写真を撮る
            </button>
            <button
              onClick={stopCamera}
              className="rounded-lg border border-gray-300 px-4 py-3 font-medium text-gray-700 hover:bg-gray-50"
            >
              キャンセル
            </button>
          </div>
        </>
      )}

      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}
```

## Additional Recommendations

### 1. Add Permission Debugging

```typescript
// Add this before getUserMedia to check permissions
const checkCameraPermission = async () => {
  try {
    const permission = await navigator.permissions.query({ name: 'camera' as PermissionName });
    console.log('Camera permission:', permission.state);

    permission.onchange = () => {
      console.log('Camera permission changed:', permission.state);
    };

    return permission.state;
  } catch (err) {
    console.error('Permission check failed:', err);
    return 'unknown';
  }
};
```

### 2. Test on Multiple iOS Versions

- iOS Safari 14+: Should work with fixes
- iOS Safari 12-13: May need additional polyfills
- WKWebView: May have additional restrictions

### 3. Add User Guidance

```typescript
<div className="rounded-lg bg-blue-50 p-4 text-sm text-blue-800">
  <p className="font-medium">📱 iPhoneをお使いの方へ：</p>
  <ul className="mt-2 list-disc space-y-1 pl-5">
    <li>初回使用時にカメラへのアクセス許可が必要です</li>
    <li>黒い画面が表示される場合は、ページを再読み込みしてください</li>
    <li>設定 → Safari → カメラ で許可を確認してください</li>
  </ul>
</div>
```

## Testing Checklist

- [ ] iPhone Safari (latest)
- [ ] iPhone Safari (iOS 14+)
- [ ] iPad Safari
- [ ] Chrome on iOS (uses WebKit, same restrictions)
- [ ] Portrait and landscape orientations
- [ ] Front and rear camera switching
- [ ] Multiple capture sessions
- [ ] Permission denied scenario
- [ ] Slow network conditions

## Performance Optimization

Current JPEG quality: `0.9` (90%)
Recommended: `0.85` (85%) - saves ~30% file size with minimal quality loss

**Estimated image sizes**:
- 1920x1080 @ 0.9 quality: ~400-600 KB
- 1920x1080 @ 0.85 quality: ~280-420 KB
- 1280x720 @ 0.85 quality: ~150-250 KB

For mobile uploads, consider adding resolution options:
```typescript
video: {
  facingMode: { ideal: "environment" },
  width: { ideal: 1280, max: 1920 },   // Lower ideal for mobile
  height: { ideal: 720, max: 1080 }
}
```

## Related Files to Update

1. `yoshikosan-frontend/components/camera-capture.tsx` - Primary fix
2. `yoshikosan-frontend/app/(dashboard)/sessions/[id]/page.tsx` - May need error handling update
3. Update OpenSpec if changing API contract (not needed for this fix)

## References

- [MDN: MediaDevices.getUserMedia()](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
- [iOS Safari Media Capture Best Practices](https://webkit.org/blog/6784/new-video-policies-for-ios/)
- [Canvas.toDataURL() Quality](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toDataURL)
