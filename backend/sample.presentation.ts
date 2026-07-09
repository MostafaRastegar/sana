import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormInstance } from "antd";
import { PaginationParams } from "papak/_modulesTypes";
import { presentationError } from "papak/utils/formErrorHandler";
import { useSearchParamsToObject } from "papak/utils/useSearchParamsToObject";
import { useInvalidQuery } from "@/utils/useInvalidQuery";
import { AlertAppService } from "./alert-app.service";
import {
  AlertAppPageCreateParams,
  CreateAlertRequest,
} from "./domains/models/AlertApp";

const AlertAppQueryKeys = {
  alertAppAlertList: "alertAppAlertList",
  alertAppAlertCreate: "alertAppAlertCreate",
  alertAppAlertRetrieve: "alertAppAlertRetrieve",
  alertAppAlertUpdate: "alertAppAlertUpdate",
  alertAppAlertDestroy: "alertAppAlertDestroy",
  alertAppPageCreate: "alertAppPageCreate",
};

export function AlertAppPresentation() {
  const Service = AlertAppService();
  const { invalidateQueriesGenerator } = useInvalidQuery();
  return {
    useAlertAppAlertList: (params?: PaginationParams) => {
      const query_params = useSearchParamsToObject();
      const mergedQueryParams = {
        ...params,
        ...query_params,
        items_per_page: query_params.page_size,
      };

      return useQuery({
        queryKey: [AlertAppQueryKeys.alertAppAlertList],
        queryFn: () => Service.alertAppAlertList(mergedQueryParams),
        enabled: Object.keys(mergedQueryParams || {}).length > 0,
      });
    },

    useAlertAppAlertCreate: (form?: FormInstance) => {
      const router = useRouter();

      return useMutation({
        mutationFn: (body: CreateAlertRequest) =>
          Service.alertAppAlertCreate(body),
        onSuccess() {
          invalidateQueriesGenerator([AlertAppQueryKeys.alertAppAlertList]);
          router.push("/dashboard/admin/alerts");
        },
        onError(error) {
          presentationError(error, form);
        },
      });
    },

    useAlertAppAlertRetrieve: () => {
      const { alerts_id } = useParams();
      return useQuery({
        queryKey: [AlertAppQueryKeys.alertAppAlertRetrieve, alerts_id],
        queryFn: () => Service.alertAppAlertRetrieve(alerts_id as string),
        enabled: !!alerts_id,
      });
    },

    useAlertAppAlertUpdate: (form?: FormInstance) => {
      const router = useRouter();
      const { alerts_id } = useParams();

      return useMutation({
        mutationFn: (body: CreateAlertRequest) =>
          Service.alertAppAlertUpdate(alerts_id as string, body),
        onSuccess() {
          invalidateQueriesGenerator([
            AlertAppQueryKeys.alertAppAlertList,
            AlertAppQueryKeys.alertAppAlertRetrieve,
          ]);
          router.push("/dashboard/admin/alerts");
        },

        onError(error) {
          presentationError(error, form);
        },
      });
    },

    useAlertAppAlertDestroy: () => {
      return useMutation({
        mutationFn: ({ id }: { id: string }) =>
          Service.alertAppAlertDestroy(id as string),
        onSuccess() {
          invalidateQueriesGenerator([
            AlertAppQueryKeys.alertAppAlertList,
            AlertAppQueryKeys.alertAppAlertRetrieve,
          ]);
        },
      });
    },

    useAlertAppAlertPageCreate: (form?: FormInstance) => {
      return useMutation({
        mutationFn: (body: AlertAppPageCreateParams) =>
          Service.alertAppPageCreate(body),
        onError(error) {
          presentationError(error, form);
        },
      });
    },
  };
}
