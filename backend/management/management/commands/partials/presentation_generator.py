from typing import Any, List, Set, Dict, Optional
from .base import BaseTsGenerator


class PresentationGenerator(BaseTsGenerator):
    """
    Generates '{app_name}.presentation.ts' containing React Query hooks
    for list, retrieve, create, update, patch and destroy operations
    based on DRF routers and serializers.
    """

    def __init__(
        self,
        app_name: str,
        app_dir: str,
        stdout: Any,
        style: Any,
        routers_list: List[Any],
        serializers_list: List[Any],
    ):
        super().__init__(app_name, app_dir, stdout, style)
        self.routers_list = routers_list
        self.serializers_list = serializers_list

    def generate(self) -> None:
        """
        Main entry point to generate the presentation file.
        """
        if not self.routers_list:
            self.stdout.write(
                self.style.WARNING(
                    f"No routers found for {self.app_name}. Skipping presentation file."
                )
            )
            return

        content: List[str] = self._build_header_imports()

        processed_model_names: Set[str] = set()
        all_hooks: List[str] = []

        for router in self.routers_list:
            for prefix, viewset_class, basename in getattr(router, "registry", []):
                model_name = basename.capitalize().replace("-", "")
                if model_name in processed_model_names:
                    continue
                processed_model_names.add(model_name)

                serializer_class = self._find_matching_serializer(
                    self.serializers_list, basename
                )
                if not serializer_class:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No serializer found for basename '{basename}' "
                            f"(model {model_name}). Skipping hooks."
                        )
                    )
                    continue

                # Determine available actions for this viewset
                actions = self._detect_actions_for_viewset(viewset_class)

                # Imports for current model
                content.extend(self._build_model_imports_block(model_name=model_name))

                # Generate hooks for this model based on available actions
                hooks_for_model = self._generate_model_hooks(
                    model_name=model_name,
                    basename=basename,
                    prefix=prefix,
                    actions=actions,
                )
                all_hooks.extend(hooks_for_model)

        # If no hooks generated at all, don't write file
        if not all_hooks:
            self.stdout.write(
                self.style.WARNING(
                    f"No presentation hooks generated for {self.app_name}."
                )
            )
            return

        # Add the hooks bodies
        content.extend(all_hooks)
        content.append("")

        # Wrap them in use<AppName>Presentation
        content.extend(
            self._build_presentation_wrapper(
                app_name=self.app_name,
                hooks=all_hooks,
            )
        )

        # Write file {app_name}.presentation.ts
        self._write_file(f"{self.app_name}.presentation.ts", "\n".join(content))

    # -------------------------------------------------------------------------
    # Header / imports
    # -------------------------------------------------------------------------
    def _build_header_imports(self) -> List[str]:
        """
        Build the static header imports for the presentation file.
        """
        return [
            'import { useParams, useRouter } from "next/navigation";',
            'import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";',
            'import type { FormInstance } from "antd";',
            'import { PaginationParams } from "@/types/pagination";',
            'import { presentationError } from "@/utils/presentationError";',
            'import { useSearchParamsToObject } from "@/hooks/useSearchParamsToObject";',
            'import { useInvalidQuery } from "@/hooks/useInvalidQuery";',
            "",
        ]

    # -------------------------------------------------------------------------
    # Serializer matching
    # -------------------------------------------------------------------------
    @staticmethod
    def _find_matching_serializer(
        serializers_list: List[Any], basename: str
    ) -> Optional[Any]:
        """
        Find a serializer whose name (without 'Serializer') matches the router basename
        (case-insensitive).
        """
        target = basename.lower()
        for ser in serializers_list:
            name = ser.__name__
            name_base = name.replace("Serializer", "").lower()
            if name_base == target:
                return ser
        return None

    # -------------------------------------------------------------------------
    # Viewset actions detection
    # -------------------------------------------------------------------------
    @staticmethod
    def _detect_actions_for_viewset(viewset_class: Any) -> Dict[str, bool]:
        """
        Detect available actions for the given viewset class.
        Returns a dict with boolean flags for list, retrieve, create, update,
        partial_update (patch), destroy.
        """
        actions = {
            "list": False,
            "retrieve": False,
            "create": False,
            "update": False,
            "partial_update": False,
            "destroy": False,
        }

        # Prefer action_map if present (like in DRF ViewSet)
        action_map = getattr(viewset_class, "action_map", None)
        if isinstance(action_map, dict):
            values = set(action_map.values())
            for key in actions.keys():
                if key in values:
                    actions[key] = True
        else:
            # Fallback: inspect methods directly
            for key in actions.keys():
                if hasattr(viewset_class, key):
                    actions[key] = True

        return actions

    # -------------------------------------------------------------------------
    # Imports for per-model
    # -------------------------------------------------------------------------
    def _build_model_imports_block(self, model_name: str) -> List[str]:
        """
        Returns import lines for a specific model.
        Example:
        import { UserModel, UserRequest } from "./app.interfaces";
        import { UserService } from "./app.services";
        """
        return [
            f'import type {model_name}Model from "./{self.app_name}.interfaces";'
            f" // adjust if you export as named",
            f'import type {model_name}Request from "./{self.app_name}.interfaces";',
            f'import {{ {model_name}Service }} from "./{self.app_name}.services";',
            "",
        ]

    # -------------------------------------------------------------------------
    # Hooks generation per model
    # -------------------------------------------------------------------------
    def _generate_model_hooks(
        self,
        model_name: str,
        basename: str,
        prefix: str,
        actions: Dict[str, bool],
    ) -> List[str]:
        """
        Generate React hooks for a given model based on available actions.
        """
        hooks: List[str] = []
        list_hook_name = f"use{model_name}List"
        retrieve_hook_name = f"use{model_name}Retrieve"
        create_hook_name = f"use{model_name}Create"
        update_hook_name = f"use{model_name}Update"
        patch_hook_name = f"use{model_name}Patch"
        destroy_hook_name = f"use{model_name}Destroy"

        # base path for redirect after create/update, etc.
        # مطابق توضیحات: /dashboard/admin/{app_name}/{basename}s
        base_route = f"/dashboard/admin/{self.app_name}/{basename}s"

        if actions.get("list"):
            hooks.extend(
                self._build_list_hook(
                    hook_name=list_hook_name,
                    model_name=model_name,
                    prefix=prefix,
                )
            )

        if actions.get("retrieve"):
            hooks.extend(
                self._build_retrieve_hook(
                    hook_name=retrieve_hook_name,
                    model_name=model_name,
                    prefix=prefix,
                )
            )

        if actions.get("create"):
            hooks.extend(
                self._build_create_hook(
                    hook_name=create_hook_name,
                    model_name=model_name,
                    base_route=base_route,
                )
            )

        if actions.get("update"):
            hooks.extend(
                self._build_update_hook(
                    hook_name=update_hook_name,
                    model_name=model_name,
                    base_route=base_route,
                )
            )

        if actions.get("partial_update"):
            hooks.extend(
                self._build_patch_hook(
                    hook_name=patch_hook_name,
                    model_name=model_name,
                    base_route=base_route,
                )
            )

        if actions.get("destroy"):
            hooks.extend(
                self._build_destroy_hook(
                    hook_name=destroy_hook_name,
                    model_name=model_name,
                    base_route=base_route,
                )
            )

        return hooks

    # -------------------------------------------------------------------------
    # Individual hook builders
    # -------------------------------------------------------------------------
    def _build_list_hook(
        self,
        hook_name: str,
        model_name: str,
        prefix: str,
    ) -> List[str]:
        """
        Builds use<Model>List hook.
        """
        return [
            f"export function {hook_name}(params?: PaginationParams) {{",
            "  const searchParams = useSearchParamsToObject();",
            "  const queryClient = useQueryClient();",
            "  const { invalidateQueriesGenerator } = useInvalidQuery();",
            "",
            "  const mergedParams = {",
            "    ...params,",
            "    ...searchParams,",
            "  };",
            "",
            "  const queryKey = [",
            f'    "{self.app_name}",',
            f'    "{prefix}",',
            '    "list",',
            "    mergedParams,",
            "  ];",
            "",
            "  const query = useQuery({",
            "    queryKey,",
            f"    queryFn: () => {model_name}Service.getList(mergedParams),",
            "  });",
            "",
            "  const invalidate = () => {",
            "    const invalidateQuery = invalidateQueriesGenerator(queryKey);",
            "    invalidateQuery(queryClient);",
            "  };",
            "",
            "  return {",
            "    ...query,",
            "    invalidate,",
            "  };",
            "}",
            "",
        ]

    def _build_retrieve_hook(
        self,
        hook_name: str,
        model_name: str,
        prefix: str,
    ) -> List[str]:
        """
        Builds use<Model>Retrieve hook.
        """
        return [
            f"export function {hook_name}() {{",
            "  const { id } = useParams();",
            "  const queryClient = useQueryClient();",
            "  const { invalidateQueriesGenerator } = useInvalidQuery();",
            "",
            "  const queryKey = [",
            f'    "{self.app_name}",',
            f'    "{prefix}",',
            '    "retrieve",',
            "    { id },",
            "  ];",
            "",
            "  const query = useQuery({",
            "    queryKey,",
            f"    queryFn: () => {model_name}Service.getById(id),",
            "    enabled: !!id,",
            "  });",
            "",
            "  const invalidate = () => {",
            "    const invalidateQuery = invalidateQueriesGenerator(queryKey);",
            "    invalidateQuery(queryClient);",
            "  };",
            "",
            "  return {",
            "    ...query,",
            "    invalidate,",
            "  };",
            "}",
            "",
        ]

    def _build_create_hook(
        self,
        hook_name: str,
        model_name: str,
        base_route: str,
    ) -> List[str]:
        """
        Builds use<Model>Create hook.
        """
        return [
            f"export function {hook_name}(form: FormInstance<{model_name}Request>) {{",
            "  const router = useRouter();",
            "  const queryClient = useQueryClient();",
            "  const { invalidateQueriesGenerator } = useInvalidQuery();",
            "",
            "  const mutation = useMutation({",
            f"    mutationFn: (data: {model_name}Request) => {model_name}Service.create(data),",
            "    onSuccess: (_data) => {",
            "      const invalidateQuery = invalidateQueriesGenerator();",
            "      invalidateQuery(queryClient);",
            f'      router.push("{base_route}");',
            "    },",
            "    onError: (error) => {",
            "      presentationError(error, form);",
            "    },",
            "  });",
            "",
            "  return mutation;",
            "}",
            "",
        ]

    def _build_update_hook(
        self,
        hook_name: str,
        model_name: str,
        base_route: str,
    ) -> List[str]:
        """
        Builds use<Model>Update hook.
        """
        return [
            f"export function {hook_name}(form: FormInstance<{model_name}Request>) {{",
            "  const { id } = useParams();",
            "  const router = useRouter();",
            "  const queryClient = useQueryClient();",
            "  const { invalidateQueriesGenerator } = useInvalidQuery();",
            "",
            "  const mutation = useMutation({",
            f"    mutationFn: (data: {model_name}Request) => {model_name}Service.update(id, data),",
            "    onSuccess: (_data) => {",
            "      const invalidateQuery = invalidateQueriesGenerator();",
            "      invalidateQuery(queryClient);",
            f'      router.push("{base_route}");',
            "    },",
            "    onError: (error) => {",
            "      presentationError(error, form);",
            "    },",
            "  });",
            "",
            "  return mutation;",
            "}",
            "",
        ]

    def _build_patch_hook(
        self,
        hook_name: str,
        model_name: str,
        base_route: str,
    ) -> List[str]:
        """
        Builds use<Model>Patch hook (partial update).
        """
        return [
            f"export function {hook_name}(form: FormInstance<Partial<{model_name}Request>>) {{",
            "  const { id } = useParams();",
            "  const router = useRouter();",
            "  const queryClient = useQueryClient();",
            "  const { invalidateQueriesGenerator } = useInvalidQuery();",
            "",
            "  const mutation = useMutation({",
            f"    mutationFn: (data: Partial<{model_name}Request>) => {model_name}Service.patch(id, data),",
            "    onSuccess: (_data) => {",
            "      const invalidateQuery = invalidateQueriesGenerator();",
            "      invalidateQuery(queryClient);",
            f'      router.push("{base_route}");',
            "    },",
            "    onError: (error) => {",
            "      presentationError(error, form);",
            "    },",
            "  });",
            "",
            "  return mutation;",
            "}",
            "",
        ]

    def _build_destroy_hook(
        self,
        hook_name: str,
        model_name: str,
        base_route: str,
    ) -> List[str]:
        """
        Builds use<Model>Destroy hook.
        """
        return [
            f"export function {hook_name}() {{",
            "  const { id } = useParams();",
            "  const router = useRouter();",
            "  const queryClient = useQueryClient();",
            "  const { invalidateQueriesGenerator } = useInvalidQuery();",
            "",
            "  const mutation = useMutation({",
            f"    mutationFn: () => {model_name}Service.delete(id),",
            "    onSuccess: (_data) => {",
            "      const invalidateQuery = invalidateQueriesGenerator();",
            "      invalidateQuery(queryClient);",
            f'      router.push("{base_route}");',
            "    },",
            "    onError: (error) => {",
            "      // معمولاً برای destroy فرم نداریم، ولی اگر داشته باشید می‌توانید اینجا هندل کنید",
            "    },",
            "  });",
            "",
            "  return mutation;",
            "}",
            "",
        ]

    # -------------------------------------------------------------------------
    # Wrapper function: use<AppName>Presentation
    # -------------------------------------------------------------------------
    def _build_presentation_wrapper(
        self,
        app_name: str,
        hooks: List[str],
    ) -> List[str]:
        """
        Wraps generated hooks into a single use<AppName>Presentation function.
        اینجا به‌صورت ساده فقط invalidateQueriesGenerator را در اختیار می‌گذارد؛
        اگر در نسخه اصلی، این تابع آبجکت خاصی برمی‌گرداند که شامل همه هوک‌هاست،
        می‌توانید لیست هوک‌ها را نیز در آبجکت return کنید.
        """
        fn_name = f"use{app_name.capitalize()}Presentation"
        return [
            f"export function {fn_name}() {{",
            "  const { invalidateQueriesGenerator } = useInvalidQuery();",
            "  return {",
            "    invalidateQueriesGenerator,",
            "    // اضافه کردن هوک‌های مورد نیاز در صورت لزوم",
            "  };",
            "}",
        ]
