/**
 * Course card for the LembreteBF page.
 *
 * Horizontal card with image thumbnail, title, and description.
 * Dark bg-gray-900/80 background.
 */
import type { BFCourseCard } from '@/types';

interface CourseCardProps {
  course: BFCourseCard;
}

export default function CourseCard({ course }: CourseCardProps) {
  return (
    <div className="flex flex-col items-start gap-4 rounded-lg bg-gray-900/80 p-4 md:flex-row">
      <div className="w-full flex-shrink-0 md:w-32">
        <img
          src={course.image}
          alt={course.title}
          className="h-auto w-full rounded"
          loading="lazy"
        />
      </div>
      <div className="flex-1">
        <h3 className="mb-2 text-lg font-bold text-white">{course.title}</h3>
        <p className="text-sm leading-relaxed text-white/70">
          {course.description}
        </p>
      </div>
    </div>
  );
}
