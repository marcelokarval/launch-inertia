/**
 * WhatsApp floating button — fixed position bottom-right.
 */
import { motion } from 'framer-motion';
import { MessageCircle } from 'lucide-react';

import type { AgrelliflixWhatsAppConfig } from '@/types';

interface WhatsAppButtonProps {
  config: AgrelliflixWhatsAppConfig;
}

export default function WhatsAppButton({ config }: WhatsAppButtonProps) {
  if (!config.enabled) return null;

  const url = `https://wa.me/${config.number}?text=${encodeURIComponent(config.message)}`;

  return (
    <motion.a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ delay: 2, type: 'spring' }}
      className="fixed bottom-20 right-4 z-40 flex items-center justify-center w-14 h-14 rounded-full shadow-xl bg-[#25D366] text-white hover:bg-[#20BD5A] transition-colors"
      aria-label="WhatsApp"
    >
      <MessageCircle size={26} />
    </motion.a>
  );
}
