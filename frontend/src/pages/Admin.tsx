import { useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { ShieldAlert, UserPlus } from 'lucide-react';
import { usersApi } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import type { UserPayload } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Skeleton, Alert, Spinner } from '../components/ui/feedback';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

const AVAILABLE_ROLES = ['viewer', 'developer', 'qa_engineer', 'approver', 'admin'];

export function AdminPage() {
  const hasPermission = useAuthStore((s) => s.hasPermission);

  if (!hasPermission('user:view')) {
    return (
      <Alert variant="destructive" title="Access denied">
        <ShieldAlert className="mb-1 inline h-4 w-4" aria-hidden="true" /> You need the{' '}
        <code className="font-mono">user:view</code> permission to manage users.
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Admin</h1>
        <p className="text-muted-foreground">Manage users, roles and permissions</p>
      </div>

      {hasPermission('user:create') && <CreateUserCard />}
      <UsersTable />
    </div>
  );
}

function CreateUserCard() {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [roles, setRoles] = useState<string[]>(['viewer']);

  const create = useMutation({
    mutationFn: () =>
      usersApi.create({
        email,
        password,
        full_name: fullName || undefined,
        roles: roles.length ? roles : undefined,
      }),
    onSuccess: (res) => {
      toast.success(`User ${res.data.email} created`);
      setEmail('');
      setPassword('');
      setFullName('');
      setRoles(['viewer']);
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      toast.error(err.response?.data?.detail || 'Failed to create user'),
  });

  function toggleRole(role: string) {
    setRoles((prev) => (prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]));
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    create.mutate();
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UserPlus className="h-4 w-4" aria-hidden="true" /> Create User
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <Input
              type="email"
              placeholder="email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              aria-label="Email"
            />
            <Input
              type="password"
              placeholder="Password (min 8 chars)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
              aria-label="Password"
            />
            <Input
              placeholder="Full name (optional)"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              aria-label="Full name"
            />
          </div>
          <fieldset className="flex flex-wrap gap-2">
            <legend className="mb-2 text-sm text-muted-foreground">Roles</legend>
            {AVAILABLE_ROLES.map((role) => (
              <button
                key={role}
                type="button"
                onClick={() => toggleRole(role)}
                aria-pressed={roles.includes(role)}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  roles.includes(role)
                    ? 'border-primary bg-primary/15 text-primary'
                    : 'border-border text-muted-foreground hover:bg-muted'
                }`}
              >
                {role}
              </button>
            ))}
          </fieldset>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? <Spinner className="h-4 w-4" /> : <UserPlus className="h-4 w-4" />}
            Create User
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function UsersTable() {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const queryClient = useQueryClient();

  const { data: users, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.list().then((res) => res.data),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['users'] });

  const setRoles = useMutation({
    mutationFn: ({ id, roles }: { id: string; roles: string[] }) => usersApi.setRoles(id, roles),
    onSuccess: () => {
      toast.success('Roles updated');
      invalidate();
    },
    onError: () => toast.error('Failed to update roles'),
  });

  const deactivate = useMutation({
    mutationFn: (id: string) => usersApi.deactivate(id),
    onSuccess: () => {
      toast.success('User deactivated');
      invalidate();
    },
    onError: () => toast.error('Failed to deactivate user'),
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6" aria-busy="true">
          <Skeleton className="h-64" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" title="Failed to load users">
        You may lack the user:view permission.
      </Alert>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Users ({users?.length ?? 0})</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Email</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Roles</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users?.map((user) => (
              <UserRow
                key={user.id}
                user={user}
                canEdit={hasPermission('user:edit')}
                canDelete={hasPermission('user:delete')}
                busy={setRoles.isPending || deactivate.isPending}
                onSetRoles={(roles) => setRoles.mutate({ id: user.id, roles })}
                onDeactivate={() => deactivate.mutate(user.id)}
              />
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function UserRow({
  user,
  canEdit,
  canDelete,
  busy,
  onSetRoles,
  onDeactivate,
}: {
  user: UserPayload;
  canEdit: boolean;
  canDelete: boolean;
  busy: boolean;
  onSetRoles: (roles: string[]) => void;
  onDeactivate: () => void;
}) {
  function handleRoleChange(role: string, checked: boolean) {
    const current = user.roles ?? [];
    const next = checked ? [...current, role] : current.filter((r) => r !== role);
    if (next.length > 0) onSetRoles(next);
  }

  return (
    <TableRow className={user.is_active === false ? 'opacity-50' : undefined}>
      <TableCell className="font-medium">{user.email}</TableCell>
      <TableCell>{user.full_name || '—'}</TableCell>
      <TableCell>
        <div className="flex flex-wrap gap-1">
          {AVAILABLE_ROLES.map((role) => {
            const has = (user.roles ?? []).includes(role);
            return canEdit ? (
              <label
                key={role}
                className={`cursor-pointer rounded-full border px-2 py-0.5 text-xs ${
                  has
                    ? 'border-primary bg-primary/15 text-primary'
                    : 'border-border text-muted-foreground'
                }`}
              >
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={has}
                  disabled={busy}
                  onChange={(e) => handleRoleChange(role, e.target.checked)}
                />
                {role}
              </label>
            ) : (
              has && (
                <Badge key={role} variant="secondary">
                  {role}
                </Badge>
              )
            );
          })}
        </div>
      </TableCell>
      <TableCell>
        <Badge variant={user.is_active === false ? 'destructive' : 'success'}>
          {user.is_active === false ? 'inactive' : 'active'}
        </Badge>
      </TableCell>
      <TableCell>
        {canDelete && user.is_active !== false && (
          <Button size="sm" variant="destructive" onClick={onDeactivate} disabled={busy}>
            Deactivate
          </Button>
        )}
      </TableCell>
    </TableRow>
  );
}
