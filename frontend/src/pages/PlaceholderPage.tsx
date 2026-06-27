import { Link, useParams } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { Button } from "../components/Button";

/**
 * Placeholder for routes implemented in Phase 6 (module detail, step, review).
 * Keeps the navigation contract stable so Phase 6 only swaps in real screens.
 */
export function PlaceholderPage({ title }: { title: string }) {
  const params = useParams();
  const id = Object.values(params)[0];
  return (
    <EmptyState
      title={title}
      body={
        id
          ? `Dieser Bereich wird in Phase 6 umgesetzt. Referenz: ${id}`
          : "Dieser Bereich wird in Phase 6 umgesetzt."
      }
      action={
        <Link to="/">
          <Button variant="secondary">Zurück zum Dashboard</Button>
        </Link>
      }
    />
  );
}
