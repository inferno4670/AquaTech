import BookShowcase from '../components/BookShowcase';

/**
 * The shelf. Deliberately outside AppShell: the authored document brings its own topbar,
 * nav and footer, and a second chrome around it would fight the effect's full-bleed stage.
 */
export default function Landing() {
  return (
    <div className="book-showcase-host">
      <BookShowcase />
    </div>
  );
}
