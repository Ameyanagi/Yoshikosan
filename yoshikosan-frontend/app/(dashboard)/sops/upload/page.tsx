"use client";

/**
 * SOP upload page.
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";

export default function UploadSOPPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [textContent, setTextContent] = useState("");
  const [images, setImages] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setImages(Array.from(e.target.files));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate that at least one of images or text content is provided
    if (images.length === 0 && !textContent.trim()) {
      setError("画像またはテキスト内容のいずれかを提供してください");
      return;
    }

    setUploading(true);

    try {
      const response = await apiClient.sops.upload({
        title,
        images,
        text_content: textContent || undefined,
      });

      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        // Redirect to SOP detail page
        router.push(`/sops/${response.data.sop_id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "アップロードに失敗しました");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-8 text-3xl font-bold">標準作業手順書アップロード</h1>

      {error && <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">SOPタイトル</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="例：機械セットアップ手順"
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">
            SOP画像（任意）
          </label>
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={handleImageChange}
            className="w-full rounded-lg border border-gray-300 px-4 py-2"
          />
          {images.length > 0 && (
            <p className="mt-2 text-sm text-gray-600">{images.length}個の画像が選択されました</p>
          )}
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">
            追加テキスト内容（任意）
          </label>
          <textarea
            value={textContent}
            onChange={(e) => setTextContent(e.target.value)}
            rows={6}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="SOPの追加テキスト内容を入力してください..."
          />
        </div>

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={uploading}
            className="flex-1 rounded-lg bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
          >
            {uploading ? "アップロード中..." : "SOPをアップロード"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-lg border border-gray-300 px-6 py-3 font-medium text-gray-700 hover:bg-gray-50"
          >
            キャンセル
          </button>
        </div>

        <div className="rounded-lg bg-blue-50 p-4 text-sm text-blue-800">
          <p className="font-medium">注意：</p>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            <li>画像またはテキスト内容のいずれか（または両方）を提供してください</li>
            <li>
              アップロード後、AIが自動的にSOPをタスク、ステップ、安全上の危険に構造化します
            </li>
            <li>処理に数分かかる場合があります</li>
          </ul>
        </div>
      </form>
    </div>
  );
}
