"use client";

import { CategorizationSchema } from "@/lib/types/candidate";

interface CategorizationSchemaViewProps {
  schema: CategorizationSchema;
}

export function CategorizationSchemaView({
  schema,
}: CategorizationSchemaViewProps) {
  const renderValue = (value: any): string => {
    if (value === null || value === undefined) {
      return "N/A";
    }
    if (Array.isArray(value)) {
      return value.length > 0 ? value.join(", ") : "N/A";
    }
    if (typeof value === "object") {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  return (
    <div className="space-y-6">
      {/* Contact Info */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold border-b pb-2">
          Contact Information
        </h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-muted-foreground">
              Full Name:
            </span>
            <p className="mt-1">{renderValue(schema.contact_info.full_name)}</p>
          </div>
          <div>
            <span className="font-medium text-muted-foreground">Email:</span>
            <p className="mt-1">{renderValue(schema.contact_info.email)}</p>
          </div>
          <div>
            <span className="font-medium text-muted-foreground">Phone:</span>
            <p className="mt-1">{renderValue(schema.contact_info.phone)}</p>
          </div>
          <div>
            <span className="font-medium text-muted-foreground">LinkedIn:</span>
            <p className="mt-1 truncate">
              {renderValue(schema.contact_info.linkedin)}
            </p>
          </div>
          {schema.contact_info.other_links &&
            schema.contact_info.other_links.length > 0 && (
              <div className="col-span-2">
                <span className="font-medium text-muted-foreground">
                  Other Links:
                </span>
                <p className="mt-1">
                  {renderValue(schema.contact_info.other_links)}
                </p>
              </div>
            )}
        </div>
      </section>

      {/* Education */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold border-b pb-2">Education</h3>
        {schema.education.length > 0 ? (
          <div className="space-y-4">
            {schema.education.map((edu, idx) => (
              <div
                key={idx}
                className="border-l-2 border-primary pl-4 space-y-2"
              >
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Degree Type:
                    </span>
                    <p className="mt-1">{renderValue(edu.degree_type)}</p>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Degree Name:
                    </span>
                    <p className="mt-1">{renderValue(edu.degree_name)}</p>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Institution:
                    </span>
                    <p className="mt-1">{renderValue(edu.institution)}</p>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Major:
                    </span>
                    <p className="mt-1">{renderValue(edu.major)}</p>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Period:
                    </span>
                    <p className="mt-1">
                      {renderValue(edu.start_date)} -{" "}
                      {renderValue(edu.end_date)}
                    </p>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Grades:
                    </span>
                    <p className="mt-1">{renderValue(edu.grades)}</p>
                  </div>
                  {edu.description && (
                    <div className="col-span-2">
                      <span className="font-medium text-muted-foreground">
                        Description:
                      </span>
                      <p className="mt-1">{renderValue(edu.description)}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No education data available
          </p>
        )}
      </section>

      {/* Experience */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold border-b pb-2">Experience</h3>
        {schema.experience.length > 0 ? (
          <div className="space-y-4">
            {schema.experience.map((exp, idx) => (
              <div
                key={idx}
                className="border-l-2 border-primary pl-4 space-y-2"
              >
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Company:
                    </span>
                    <p className="mt-1 font-semibold">
                      {renderValue(exp.company_name)}
                    </p>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Role:
                    </span>
                    <p className="mt-1 font-semibold">
                      {renderValue(exp.role_title)}
                    </p>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Location:
                    </span>
                    <p className="mt-1">{renderValue(exp.location)}</p>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Period:
                    </span>
                    <p className="mt-1">
                      {renderValue(exp.start_date)} -{" "}
                      {renderValue(exp.end_date)}
                    </p>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Duration:
                    </span>
                    <p className="mt-1">
                      {renderValue(exp.duration_years)} years
                    </p>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Industry:
                    </span>
                    <p className="mt-1">{renderValue(exp.industry_primary)}</p>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Company Type:
                    </span>
                    <p className="mt-1">{renderValue(exp.company_type)}</p>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">
                      Internship:
                    </span>
                    <p className="mt-1">{exp.is_internship ? "Yes" : "No"}</p>
                  </div>
                  {exp.industries_secondary.length > 0 && (
                    <div className="col-span-2">
                      <span className="font-medium text-muted-foreground">
                        Secondary Industries:
                      </span>
                      <p className="mt-1">
                        {renderValue(exp.industries_secondary)}
                      </p>
                    </div>
                  )}
                  {exp.hard_skills.length > 0 && (
                    <div className="col-span-2">
                      <span className="font-medium text-muted-foreground">
                        Hard Skills:
                      </span>
                      <p className="mt-1">{renderValue(exp.hard_skills)}</p>
                    </div>
                  )}
                  {exp.soft_skills.length > 0 && (
                    <div className="col-span-2">
                      <span className="font-medium text-muted-foreground">
                        Soft Skills:
                      </span>
                      <p className="mt-1">{renderValue(exp.soft_skills)}</p>
                    </div>
                  )}
                  {exp.summary && (
                    <div className="col-span-2">
                      <span className="font-medium text-muted-foreground">
                        Summary:
                      </span>
                      <p className="mt-1">{renderValue(exp.summary)}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No experience data available
          </p>
        )}
      </section>

      {/* Skills Summary */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold border-b pb-2">Skills Summary</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-muted-foreground">
              Hard Skills:
            </span>
            <p className="mt-1">
              {renderValue(schema.skills_summary.hard_skills_overall)}
            </p>
          </div>
          <div>
            <span className="font-medium text-muted-foreground">
              Soft Skills:
            </span>
            <p className="mt-1">
              {renderValue(schema.skills_summary.soft_skills_overall)}
            </p>
          </div>
          <div>
            <span className="font-medium text-muted-foreground">
              Software Knowledge:
            </span>
            <p className="mt-1">
              {renderValue(schema.skills_summary.software_knowledge)}
            </p>
          </div>
          <div>
            <span className="font-medium text-muted-foreground">
              Languages:
            </span>
            <p className="mt-1">
              {renderValue(schema.skills_summary.languages)}
            </p>
          </div>
          <div className="col-span-2">
            <span className="font-medium text-muted-foreground">
              Interests:
            </span>
            <p className="mt-1">
              {renderValue(schema.skills_summary.interests)}
            </p>
          </div>
          {schema.skills_summary.other_attributes && (
            <div className="col-span-2">
              <span className="font-medium text-muted-foreground">
                Other Attributes:
              </span>
              <p className="mt-1">
                {renderValue(schema.skills_summary.other_attributes)}
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Meta Information */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold border-b pb-2">Career Metrics</h3>
        <div className="space-y-4">
          <div>
            <span className="font-medium text-muted-foreground">
              Total Experience:
            </span>
            <p className="mt-1 text-2xl font-bold">
              {renderValue(schema.meta.total_experience_years)} years
            </p>
          </div>

          {schema.meta.experience_by_role.length > 0 && (
            <div>
              <span className="font-medium text-muted-foreground">
                Experience by Role:
              </span>
              <div className="mt-2 space-y-1">
                {schema.meta.experience_by_role.map((role, idx) => (
                  <p key={idx} className="text-sm">
                    {renderValue(role.role_family)}:{" "}
                    {renderValue(role.total_years)} years
                  </p>
                ))}
              </div>
            </div>
          )}

          {schema.meta.industry_primary_summary.length > 0 && (
            <div>
              <span className="font-medium text-muted-foreground">
                Primary Industries:
              </span>
              <div className="mt-2 space-y-1">
                {schema.meta.industry_primary_summary.map((industry, idx) => (
                  <p key={idx} className="text-sm">
                    {renderValue(industry.industry)}:{" "}
                    {renderValue(industry.total_years)} years
                  </p>
                ))}
              </div>
            </div>
          )}

          {schema.meta.industry_secondary_summary.length > 0 && (
            <div>
              <span className="font-medium text-muted-foreground">
                Secondary Industries:
              </span>
              <div className="mt-2 space-y-1">
                {schema.meta.industry_secondary_summary.map((industry, idx) => (
                  <p key={idx} className="text-sm">
                    {renderValue(industry.industry)}:{" "}
                    {renderValue(industry.total_years)} years
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
