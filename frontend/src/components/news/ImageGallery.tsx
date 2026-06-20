import type { NewsImage } from '../../types';

interface Props {
  images: NewsImage[];
}

export default function ImageGallery({ images }: Props) {
  if (images.length === 0) return null;
  return (
    <div className="bg-white rounded-xl border p-5">
      <h3 className="font-semibold text-gray-900 mb-3">配图</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {images.map((img) => (
          <a key={img.id} href={`/images/${img.local_path.split('/').pop()}`} target="_blank" rel="noopener noreferrer">
            <img
              src={`/images/${img.local_path.split('/').pop()}`}
              alt={img.image_url}
              className="w-full h-32 object-cover rounded-lg border hover:opacity-90 transition-opacity"
            />
          </a>
        ))}
      </div>
    </div>
  );
}
