/**
 * AgreliFlix/Index — CPL video lesson series page.
 *
 * Receives full config as Inertia props (server-parsed from Django).
 * Orchestrates all hooks and components for the Netflix-style video player.
 *
 * Adapted from legacy agrelliflix-content.tsx — S3 loading logic eliminated,
 * config arrives as server-rendered props.
 *
 * Max 150 lines.
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import { Head } from '@inertiajs/react';
import { Toaster } from 'react-hot-toast';

import type { AgrelliflixPageProps, AgrelliflixEpisode } from '@/types';
import {
  useVideoProgress,
  useEpisodeUnlocks,
  useAchievements,
  useIsMobile,
  useAgrelliflixStorage,
} from '@/hooks/agrelliflix';

import HeroPlayer from '@/components/agrelliflix/HeroPlayer';
import MiniPlayer from '@/components/agrelliflix/MiniPlayer';
import SocialProof from '@/components/agrelliflix/SocialProof';
import FloatingCTA from '@/components/agrelliflix/FloatingCTA';
import WhatsAppButton from '@/components/agrelliflix/WhatsAppButton';
import AchievementBadge from '@/components/agrelliflix/AchievementBadge';

export default function AgrelliFlix({ config, initial_episode_id }: AgrelliflixPageProps) {
  const { theme, episodes, social_proof, cart, whatsapp, banner_urls, achievements: achievementsConfig } = config;

  // Pick initial episode
  const startEp = episodes.find((e) => e.id === initial_episode_id) ?? episodes[0];
  const [currentEpisode, setCurrentEpisode] = useState<AgrelliflixEpisode>(startEp);
  const [showCTA, setShowCTA] = useState(false);
  const [ctaDismissed, setCtaDismissed] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showMiniPlayer, setShowMiniPlayer] = useState(false);

  const playerRef = useRef<HTMLDivElement>(null);
  const isMobile = useIsMobile();

  const { progress, saveProgress, hasWatchedAll } = useVideoProgress();
  const { unlockedEpisodes } = useEpisodeUnlocks(progress, episodes);
  const { achievements, unlockAchievement, hasAchievement } = useAchievements(achievementsConfig);
  useAgrelliflixStorage(); // Initialize gamification storage

  // Aula 3 live date check — CTA only appears after this
  const isAfterAula3 = (() => {
    const aula3 = episodes.find((e) => e.id === 3);
    return aula3 ? new Date() >= new Date(aula3.live_date) : false;
  })();

  // Mini-player on mobile scroll
  useEffect(() => {
    if (!isMobile || !isPlaying) { setShowMiniPlayer(false); return; }
    const handleScroll = () => {
      if (!playerRef.current) return;
      setShowMiniPlayer(playerRef.current.getBoundingClientRect().bottom < 0);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [isMobile, isPlaying]);

  // Auto-show CTA after aula 3
  useEffect(() => {
    if (isAfterAula3 && !ctaDismissed) setShowCTA(true);
  }, [isAfterAula3, ctaDismissed]);

  const handleProgress = useCallback(
    (currentTime: number, duration: number, pct: number) => {
      setIsPlaying(true);
      const completed = saveProgress(currentEpisode.id, currentTime, duration);
      // Flash CTA at 60%
      if (isAfterAula3 && !ctaDismissed && pct >= 60 && pct < 61) {
        setShowCTA(true);
        setTimeout(() => setShowCTA(false), 10000);
      }
      // Completionist achievement
      if (completed && !hasAchievement('completionist') && hasWatchedAll(episodes.length)) {
        unlockAchievement('completionist');
      }
    },
    [currentEpisode, saveProgress, isAfterAula3, ctaDismissed, hasAchievement, hasWatchedAll, episodes.length, unlockAchievement],
  );

  const handleComplete = useCallback(() => {
    setIsPlaying(false);
    if (isAfterAula3 && !ctaDismissed) setShowCTA(true);
  }, [isAfterAula3, ctaDismissed]);

  const handleEpisodeClick = useCallback(
    (ep: AgrelliflixEpisode) => {
      if (unlockedEpisodes.includes(ep.id) || ep.is_live_pending) {
        setCurrentEpisode(ep);
        setShowMiniPlayer(false);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    },
    [unlockedEpisodes],
  );

  // Dynamic CTA URL based on current episode
  const ctaUrl = currentEpisode.id >= 3 ? banner_urls.aulas_3_4 : banner_urls.aulas_1_2;
  const ctaText = cart.button_text || 'Quero Minha Vaga';

  return (
    <>
      <Head title={`${config.branding.series_title} - ${currentEpisode.title}`} />

      {/* CSS custom properties for Netflix theme */}
      <div
        className="min-h-screen"
        style={{
          backgroundColor: theme.black_deep,
          '--aflix-red': theme.red_primary,
          '--aflix-gold': theme.gold_accent,
        } as React.CSSProperties}
      >
        <Toaster position="top-right" />

        {/* Mini Player (mobile sticky) */}
        {isMobile && (
          <MiniPlayer
            episode={currentEpisode}
            isVisible={showMiniPlayer}
            onClose={() => { setShowMiniPlayer(false); setIsPlaying(false); }}
            onResume={() => { setShowMiniPlayer(false); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
            redPrimary={theme.red_primary}
          />
        )}

        {/* Main Player */}
        <div ref={playerRef}>
          <HeroPlayer
            episode={currentEpisode}
            episodes={episodes}
            unlockedEpisodes={unlockedEpisodes}
            progress={progress}
            initialViewers={social_proof.initial_viewers}
            ctaText={ctaText}
            ctaUrl={ctaUrl}
            theme={theme}
            onEpisodeClick={handleEpisodeClick}
            onProgressUpdate={handleProgress}
            onVideoComplete={handleComplete}
          />
        </div>

        {/* Social Proof */}
        <section className="mt-4 py-8 px-4 border-y border-white/10" style={{ backgroundColor: `${theme.grey_dark}80` }}>
          <div className="max-w-6xl mx-auto">
            <SocialProof config={social_proof} theme={theme} />
          </div>
        </section>

        {/* Achievements gallery */}
        {Object.keys(achievementsConfig).length > 0 && (
          <section className="py-8 px-4">
            <div className="max-w-4xl mx-auto">
              <h3 className="text-white/60 text-xs uppercase tracking-wider mb-4 text-center">Conquistas</h3>
              <div className="grid grid-cols-3 sm:grid-cols-5 gap-3">
                {Object.values(achievementsConfig).map((a) => (
                  <AchievementBadge key={a.id} achievement={a} isUnlocked={achievements.includes(a.id)} goldAccent={theme.gold_accent} />
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Floating CTA */}
        {isAfterAula3 && (
          <FloatingCTA
            isVisible={showCTA}
            text={ctaText}
            url={ctaUrl}
            onClose={() => { setShowCTA(false); setCtaDismissed(true); }}
            redPrimary={theme.red_primary}
          />
        )}

        {/* WhatsApp */}
        <WhatsAppButton config={whatsapp} />
      </div>
    </>
  );
}
