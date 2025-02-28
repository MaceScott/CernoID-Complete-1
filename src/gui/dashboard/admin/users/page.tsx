"use client"

import { useState } from "react"
import { User } from "@/types"
import DataTable from "@/components/ui/data-table"
import { Button } from "@/components/ui/Button"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import Alert from "@/components/ui/Alert"
import { 
  UserPlus,
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  MoreVertical
} from "lucide-react"

// Mock data - replace with API call
const mockUsers: User[] = [
  {
    id: "1",
    name: "Mace Scott",
    email: "macescott@gmail.com",
    role: "admin",
    status: "active",
    createdAt: "2024-01-01T00:00:00Z",
    lastLogin: "2024-02-14T15:30:00Z"
  },
  {
    id: "2",
    name: "John Doe",
    email: "john@example.com",
    role: "user",
    status: "active",
    createdAt: "2024-01-15T00:00:00Z",
    lastLogin: "2024-02-13T10:20:00Z"
  },
  // Add more mock users...
]

export default function UsersPage() {
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [error, setError] = useState<string | null>(null)

  const columns = [
    { key: "name", title: "Name" },
    { key: "email", title: "Email" },
    {
      key: "role",
      title: "Role",
      render: (user: User) => (
        <div className="flex items-center">
          {user.role === "admin" ? (
            <Shield className="mr-2 h-4 w-4 text-primary" />
          ) : null}
          {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
        </div>
      )
    },
    {
      key: "status",
      title: "Status",
      render: (user: User) => (
        <div className="flex items-center">
          {user.status === "active" ? (
            <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
          ) : (
            <XCircle className="mr-2 h-4 w-4 text-red-500" />
          )}
          {user.status.charAt(0).toUpperCase() + user.status.slice(1)}
        </div>
      )
    },
    {
      key: "lastLogin",
      title: "Last Login",
      render: (user: User) => (
        <div className="flex items-center">
          <Clock className="mr-2 h-4 w-4 text-muted-foreground" />
          {new Date(user.lastLogin).toLocaleDateString()}
        </div>
      )
    },
    {
      key: "actions",
      title: "",
      render: (user: User) => (
        <Button variant="ghost" size="sm">
          <MoreVertical className="h-4 w-4" />
        </Button>
      )
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">User Management</h1>
        <Button>
          <UserPlus className="mr-2 h-4 w-4" />
          Add User
        </Button>
      </div>

      {error && (
        <Alert variant="error">
          {error}
        </Alert>
      )}

      <Card>
        <CardContent className="p-6">
          <DataTable
            data={mockUsers}
            columns={columns}
            searchable
            onRowClick={setSelectedUser}
          />
        </CardContent>
      </Card>
    </div>
  )
} 