/**
 * /placement: the placement check on a page of its own, for an account that
 * skipped it at sign-up (the dashboard offers it). The same twelve problems
 * and the same component as the sign-up step (components/Amc/Placement.tsx),
 * pitched at the contest the study plan is for.
 */
import { useNavigate } from 'react-router-dom';
import { ErrorState, Loading } from '@/components';
import { Placement } from '@/components/Amc/Placement';
import { useApi, useDocumentTitle } from '@/hooks';
import { amc } from '@/services/amc';
import '@/styles/amc.css';

export default function PlacementPage() {
  useDocumentTitle('Find your level');
  const navigate = useNavigate();
  const { data, error, loading, reload } = useApi(() => amc.dashboard(), []);
  if (loading && !data) return <Loading label="Getting ready" />;
  if (error || !data) return <ErrorState message={error ?? 'Could not load the check.'} onRetry={reload} />;
  return (
    <div className="amc-page am-place-page">
      <section className="am-card am-place-card">
        <Placement level={data.plan?.target ?? data.target} onDone={() => navigate('/dashboard')} />
      </section>
    </div>
  );
}
