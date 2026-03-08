"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { FadeInSection } from "@/components/FadeInSection";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { InquiryCreateRequest } from "@/types/inquiry";
import { User, Mail, Phone, Calendar, ClipboardList, MessageSquare, AlertCircle, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";

export function InquiryForm() {
  const { t } = useTranslation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const [formData, setFormData] = useState<Partial<InquiryCreateRequest>>({
    name: "",
    email: "",
    phone: "",
    age: 18,
    preferredDate: "",
    plan: "full",
    message: ""
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: name === 'age' ? parseInt(value) || 0 : value }));
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: "" }));
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.name) newErrors.name = t("form.errorName", "Name is required");
    if (!formData.email) newErrors.email = t("form.errorEmail", "Email is required");
    if (!formData.phone) newErrors.phone = t("form.errorPhone", "Phone is required");
    if (!formData.age) newErrors.age = t("form.errorAge", "Age is required");
    if (!formData.plan) newErrors.plan = t("form.errorPlan", "Plan is required");
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    
    setIsSubmitting(true);
    try {
      await api.post("/api/inquiries", formData);
      toast.success(t("form.success", "Your inquiry has been submitted. We will contact you shortly."));
      setFormData({
        name: "", email: "", phone: "", age: 18, preferredDate: "", plan: "full", message: ""
      });
      setErrors({});
    } catch (error) {
      toast.error(t("form.error", "Failed to submit inquiry. Please try again."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section id="inquiry" className="bg-[#FAFAF9] py-28 md:py-36">
      <div className="container mx-auto px-6 max-w-2xl">
        <FadeInSection>
          <div className="text-center mb-12">
            <h2 className="text-[32px] md:text-[40px] font-bold tracking-tight text-[#2C2825] mb-4">
              {t("form.title", "Start Your Consultation")}
            </h2>
            <p className="text-[#6B6660] text-[17px] mb-8 leading-relaxed">
              {t("form.description", "Fill out the form below to schedule a free initial consultation with our visa experts.")}
            </p>
          </div>
        </FadeInSection>

        <div className="flex flex-col gap-8">
          {/* Contact Card */}
          <FadeInSection delay={100}>
            <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-[#2C2825]/6 grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
              <div className="flex flex-col items-center">
                <div className="w-10 h-10 bg-[#F5F3F0] rounded-full flex items-center justify-center mb-3">
                  <Phone className="w-4 h-4 text-[#8A6420]" />
                </div>
                <h4 className="font-semibold text-[#2C2825] mb-1">{t("form.contact.phone", "Phone")}</h4>
                <p className="text-sm text-[#6B6660]">+82 10 0000 0000</p>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-10 h-10 bg-[#F5F3F0] rounded-full flex items-center justify-center mb-3">
                  <Mail className="w-4 h-4 text-[#8A6420]" />
                </div>
                <h4 className="font-semibold text-[#2C2825] mb-1">{t("form.contact.email", "Email")}</h4>
                <p className="text-sm text-[#6B6660]">contact@moku.com</p>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-10 h-10 bg-[#F5F3F0] rounded-full flex items-center justify-center mb-3">
                  <MapPin className="w-4 h-4 text-[#8A6420]" />
                </div>
                <h4 className="font-semibold text-[#2C2825] mb-1">{t("form.contact.office", "Office")}</h4>
                <p className="text-sm text-[#6B6660]">{t("form.contact.location", "Seoul, South Korea")}</p>
              </div>
            </div>
          </FadeInSection>

          {/* Form Card */}
          <FadeInSection delay={200}>
            <form onSubmit={onSubmit} className="bg-white rounded-2xl p-8 sm:p-10 shadow-sm border border-[#2C2825]/6 space-y-6">
              <div className="space-y-2">
                <label className="flex items-center text-[15px] font-bold text-[#2C2825]">
                  <User className="w-4 h-4 mr-2 text-[#8A6420]" />
                  {t("form.name", "Full Name")} <span className="text-red-500 ml-1">*</span>
                </label>
                <Input required name="name" value={formData.name} onChange={handleChange} placeholder={t("form.namePlaceholder", "John Doe")} className={cn("bg-white focus:border-[#B8935F] focus:ring-1 focus:ring-[#B8935F] rounded-lg py-5 h-auto text-[15px] transition-colors", errors.name ? "border-red-500" : "border-[#2C2825]/10")} />
                {errors.name && <p role="alert" className="flex items-center text-red-500 text-sm mt-1"><AlertCircle className="w-4 h-4 mr-1"/>{errors.name}</p>}
              </div>

              <div className="space-y-2">
                <label className="flex items-center text-[15px] font-bold text-[#2C2825]">
                  <Mail className="w-4 h-4 mr-2 text-[#8A6420]" />
                  {t("form.email", "Email Address")} <span className="text-red-500 ml-1">*</span>
                </label>
                <Input required type="email" name="email" value={formData.email} onChange={handleChange} placeholder={t("form.emailPlaceholder", "john@example.com")} className={cn("bg-white focus:border-[#B8935F] focus:ring-1 focus:ring-[#B8935F] rounded-lg py-5 h-auto text-[15px] transition-colors", errors.email ? "border-red-500" : "border-[#2C2825]/10")} />
                {errors.email && <p role="alert" className="flex items-center text-red-500 text-sm mt-1"><AlertCircle className="w-4 h-4 mr-1"/>{errors.email}</p>}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="flex items-center text-[15px] font-bold text-[#2C2825]">
                    <Phone className="w-4 h-4 mr-2 text-[#8A6420]" />
                    {t("form.phone", "Phone Number")} <span className="text-red-500 ml-1">*</span>
                  </label>
                  <Input required type="tel" name="phone" value={formData.phone} onChange={handleChange} placeholder={t("form.phonePlaceholder", "+1 234 567 8900")} className={cn("bg-white focus:border-[#B8935F] focus:ring-1 focus:ring-[#B8935F] rounded-lg py-5 h-auto text-[15px] transition-colors", errors.phone ? "border-red-500" : "border-[#2C2825]/10")} />
                  {errors.phone && <p role="alert" className="flex items-center text-red-500 text-sm mt-1"><AlertCircle className="w-4 h-4 mr-1"/>{errors.phone}</p>}
                </div>

                <div className="space-y-2">
                  <label className="flex items-center text-[15px] font-bold text-[#2C2825]">
                    <User className="w-4 h-4 mr-2 text-[#8A6420]" />
                    {t("form.age", "Age")} <span className="text-red-500 ml-1">*</span>
                  </label>
                  <Input required type="number" min={18} max={35} name="age" value={formData.age} onChange={handleChange} placeholder="25" className={cn("bg-white focus:border-[#B8935F] focus:ring-1 focus:ring-[#B8935F] rounded-lg py-5 h-auto text-[15px] transition-colors", errors.age ? "border-red-500" : "border-[#2C2825]/10")} />
                  {errors.age && <p role="alert" className="flex items-center text-red-500 text-sm mt-1"><AlertCircle className="w-4 h-4 mr-1"/>{errors.age}</p>}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="flex items-center text-[15px] font-bold text-[#2C2825]">
                    <Calendar className="w-4 h-4 mr-2 text-[#8A6420]" />
                    {t("form.preferredDate", "Preferred Date")}
                  </label>
                  <Input type="date" name="preferredDate" value={formData.preferredDate} onChange={handleChange} className="bg-white border-[#2C2825]/10 focus:border-[#B8935F] focus:ring-1 focus:ring-[#B8935F] rounded-lg py-5 h-auto text-[15px] transition-colors" />
                </div>

                <div className="space-y-2">
                  <label className="flex items-center text-[15px] font-bold text-[#2C2825]">
                    <ClipboardList className="w-4 h-4 mr-2 text-[#8A6420]" />
                    {t("form.plan", "Support Plan")} <span className="text-red-500 ml-1">*</span>
                  </label>
                  <Select value={formData.plan} onValueChange={(val) => {
                    setFormData(p => ({ ...p, plan: val }));
                    setErrors(prev => ({ ...prev, plan: "" }));
                  }}>
                    <SelectTrigger className={cn("bg-white focus:border-[#B8935F] focus:ring-1 focus:ring-[#B8935F] rounded-lg py-5 h-auto text-[15px] w-full transition-colors", errors.plan ? "border-red-500" : "border-[#2C2825]/10")}>
                      <SelectValue placeholder={t("form.planPlaceholder", "Select a plan")} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="document">{t("form.planDocument", "Document Only")}</SelectItem>
                      <SelectItem value="full">{t("form.planFull", "Full Support")}</SelectItem>
                      <SelectItem value="vip">{t("form.planVIP", "VIP + Settlement")}</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.plan && <p role="alert" className="flex items-center text-red-500 text-sm mt-1"><AlertCircle className="w-4 h-4 mr-1"/>{errors.plan}</p>}
                </div>
              </div>

              <div className="space-y-2 pb-2">
                <label className="flex items-center text-[15px] font-bold text-[#2C2825]">
                  <MessageSquare className="w-4 h-4 mr-2 text-[#8A6420]" />
                  {t("form.message", "Additional Message")}
                </label>
                <Textarea name="message" value={formData.message} onChange={handleChange} placeholder={t("form.messagePlaceholder", "Tell us about your plans or timeline...")} rows={4} className="bg-white border-[#2C2825]/10 focus:border-[#B8935F] focus:ring-1 focus:ring-[#B8935F] rounded-lg p-4 text-[15px] resize-none transition-colors" />
              </div>

              <Button type="submit" disabled={isSubmitting} className="w-full bg-[#B8935F] text-white hover:bg-[#9E7030] py-6 rounded-full text-[17px] font-semibold h-auto shadow-md transition-all">
                {isSubmitting ? t("form.submitting", "Submitting...") : t("form.submit", "Submit Inquiry")}
              </Button>
            </form>
          </FadeInSection>
        </div>
      </div>
    </section>
  );
}
