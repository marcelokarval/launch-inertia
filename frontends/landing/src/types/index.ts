/**
 * Landing frontend types.
 *
 * These types represent data passed from Django landing views as Inertia props.
 * Keep in sync with backend view return values.
 */

/** Shared props injected by InertiaShareMiddleware (if any apply to landing) */
export interface SharedProps {
  flash?: {
    success?: string;
    error?: string;
    warning?: string;
    info?: string;
  };
}

/** Props for the Home/Index placeholder page */
export interface HomeProps extends SharedProps {
  title: string;
  description: string;
}
