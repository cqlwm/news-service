interface Props {
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({ message, onRetry }: Props) {
  return (
    <div className="text-center py-12">
      <div className="text-5xl mb-4">⚠️</div>
      <p className="text-red-600 font-medium">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">
          重试
        </button>
      )}
    </div>
  );
}
