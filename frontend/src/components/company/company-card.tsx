import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Company } from "@/types";
import { CompanyStatus } from "@/types";
import { ArrowRight, Building2 } from "lucide-react";

function statusVariant(status: CompanyStatus) {
  switch (status) {
    case CompanyStatus.ACTIVE:
      return "success" as const;
    case CompanyStatus.PAUSED:
      return "warning" as const;
    case CompanyStatus.SUSPENDED:
      return "destructive" as const;
    default:
      return "secondary" as const;
  }
}

interface CompanyCardProps {
  company: Company;
}

export function CompanyCard({ company }: CompanyCardProps) {
  return (
    <Card className="group hover:border-primary/50 transition-colors">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <Building2 className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">{company.name}</CardTitle>
              <CardDescription className="text-xs">/{company.slug}</CardDescription>
            </div>
          </div>
          <Badge variant={statusVariant(company.status)}>
            {company.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-2">
          {company.mission}
        </p>
      </CardContent>
      <CardFooter>
        <Link href={`/dashboard/${company.id}`} className="w-full">
          <Button variant="ghost" className="w-full justify-between group-hover:text-primary">
            Open Dashboard
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </CardFooter>
    </Card>
  );
}
