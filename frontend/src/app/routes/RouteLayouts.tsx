import { Outlet, Navigate } from "react-router-dom";
import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { useMembershipQuery } from "@/features/household/api/queries";
import { useViewerQuery } from "@/features/viewer/api/queries";
import { Button } from "@/shared/ui/Button/Button";
import { FullPageState } from "@/shared/ui/FullPageState/FullPageState";

function QueryErrorState({
  description,
  onRetry,
}: {
  description: string;
  onRetry: () => void;
}) {
  return (
    <FullPageState
      title="We hit a loading problem"
      description={description}
      actions={
        <Button onClick={onRetry} variant="secondary">
          Try again
        </Button>
      }
    />
  );
}

export function PublicOnlyLayout() {
  const { isLoading, user } = useAuthSession();
  const shouldBootstrap = Boolean(user?.emailVerified);
  const viewerQuery = useViewerQuery({ enabled: shouldBootstrap });
  const membershipQuery = useMembershipQuery({
    enabled: shouldBootstrap && viewerQuery.isSuccess,
  });

  if (isLoading) {
    return <FullPageState title="Checking your session" />;
  }

  if (!user) {
    return <Outlet />;
  }

  if (!user.emailVerified) {
    return <Navigate replace to="/verify-email" />;
  }

  if (viewerQuery.isLoading || membershipQuery.isLoading) {
    return <FullPageState title="Preparing your workspace" />;
  }

  if (viewerQuery.isError) {
    return (
      <QueryErrorState
        description="We could not load your profile. Please try again."
        onRetry={() => void viewerQuery.refetch()}
      />
    );
  }

  if (membershipQuery.isError) {
    return (
      <QueryErrorState
        description="We could not check your household membership."
        onRetry={() => void membershipQuery.refetch()}
      />
    );
  }

  return <Navigate replace to={membershipQuery.data ? "/dashboard" : "/household/setup"} />;
}

export function EmailVerificationLayout() {
  const { isLoading, user } = useAuthSession();
  const shouldCheckMembership = Boolean(user?.emailVerified);
  const viewerQuery = useViewerQuery({ enabled: shouldCheckMembership });
  const membershipQuery = useMembershipQuery({
    enabled: shouldCheckMembership && viewerQuery.isSuccess,
  });

  if (isLoading) {
    return <FullPageState title="Checking your session" />;
  }

  if (!user) {
    return <Navigate replace to="/login" />;
  }

  if (!user.emailVerified) {
    return <Outlet />;
  }

  if (viewerQuery.isLoading || membershipQuery.isLoading) {
    return <FullPageState title="Preparing your workspace" />;
  }

  return <Navigate replace to={membershipQuery.data ? "/dashboard" : "/household/setup"} />;
}

export function VerifiedSessionLayout() {
  const { isLoading, user } = useAuthSession();
  const viewerQuery = useViewerQuery({ enabled: Boolean(user?.emailVerified) });

  if (isLoading) {
    return <FullPageState title="Checking your session" />;
  }

  if (!user) {
    return <Navigate replace to="/login" />;
  }

  if (!user.emailVerified) {
    return <Navigate replace to="/verify-email" />;
  }

  if (viewerQuery.isLoading) {
    return <FullPageState title="Loading your profile" />;
  }

  if (viewerQuery.isError) {
    return (
      <QueryErrorState
        description="We could not load your account details."
        onRetry={() => void viewerQuery.refetch()}
      />
    );
  }

  return <Outlet />;
}

export function HouseholdSetupLayout() {
  const membershipQuery = useMembershipQuery({ enabled: true });

  if (membershipQuery.isLoading) {
    return <FullPageState title="Checking your household status" />;
  }

  if (membershipQuery.isError) {
    return (
      <QueryErrorState
        description="We could not load your household membership."
        onRetry={() => void membershipQuery.refetch()}
      />
    );
  }

  if (membershipQuery.data) {
    return <Navigate replace to="/dashboard" />;
  }

  return <Outlet />;
}

export function HouseholdRequiredLayout() {
  const membershipQuery = useMembershipQuery({ enabled: true });

  if (membershipQuery.isLoading) {
    return <FullPageState title="Checking your household status" />;
  }

  if (membershipQuery.isError) {
    return (
      <QueryErrorState
        description="We could not load your household membership."
        onRetry={() => void membershipQuery.refetch()}
      />
    );
  }

  if (!membershipQuery.data) {
    return <Navigate replace to="/household/setup" />;
  }

  return <Outlet />;
}
