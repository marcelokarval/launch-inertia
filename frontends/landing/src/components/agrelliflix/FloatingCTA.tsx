/**
 * Floating CTA banner — appears after episode completion threshold.
 */
import { motion, AnimatePresence } from 'framer-motion';
import { X, ShoppingCart } from 'lucide-react';

interface FloatingCTAProps {
  isVisible: boolean;
  text: string;
  url: string;
  onClose: () => void;
  redPrimary: string;
}

export default function FloatingCTA({
  isVisible,
  text,
  url,
  onClose,
  redPrimary,
}: FloatingCTAProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          className="fixed bottom-4 left-4 right-4 z-50 flex items-center gap-3 p-4 rounded-xl shadow-2xl"
          style={{ backgroundColor: '#141414', border: `1px solid ${redPrimary}` }}
        >
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center gap-2 px-4 py-2.5 rounded-lg text-white font-semibold text-sm transition-transform hover:scale-[1.02]"
            style={{ backgroundColor: redPrimary }}
          >
            <ShoppingCart size={16} />
            {text}
          </a>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-white/40 hover:text-white"
          >
            <X size={18} />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
