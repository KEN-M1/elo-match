import { InviteClient } from "./invite-client";

export default function InvitePage({ params }: { params: { token: string } }) {
  return <InviteClient token={params.token} />;
}
