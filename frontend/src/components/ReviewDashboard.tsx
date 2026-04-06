import ShortlistView from './ShortlistView';

export default function ReviewDashboard({ campaignId }: { campaignId: string }) {
  return (
    <div className="glass-panel">
      <ShortlistView />
    </div>
  );
}
