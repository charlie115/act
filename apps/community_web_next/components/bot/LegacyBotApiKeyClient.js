"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import Grid from "@mui/material/Grid";
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";

import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { DateTime } from "luxon";
import truncate from "lodash/truncate";

import {
  useDeleteExchangeApiKeyMutation,
  useGetExchangeApiKeyQuery,
  useGetNodesQuery,
  usePostExchangeApiKeyMutation,
} from "redux/api/drf/tradecore";

import DeleteAlert from "components/DeleteAlert";
import ReactTableUI from "components/ReactTableUI";
import renderActionIconCell from "components/tables/common/renderActionIconCell";

export default function LegacyBotApiKeyClient({
  marketCodeCombination,
  tradeConfigAllocations,
}) {
  const { t } = useTranslation();
  const [deleteAlert, setDeleteAlert] = useState(null);
  const [marketCodeForm, setMarketCodeForm] = useState(null);
  const [showPassphrase, setShowPassphrase] = useState(false);
  const [showSecretKey, setShowSecretKey] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const handleCloseDialog = () => {
    setMarketCodeForm(null);
    setSubmitError(null);
    setShowPassphrase(false);
    setShowSecretKey(false);
    reset();
  };

  const { data: exchangeApiKeys } = useGetExchangeApiKeyQuery({
    tradeConfigUuid: marketCodeCombination.tradeConfigUuid,
  });
  const { data: nodes } = useGetNodesQuery();

  const allocatedNodeId = tradeConfigAllocations?.find(
    (item) => item.uuid === marketCodeCombination.tradeConfigUuid
  )?.node;
  const allocatedNodeUrl = nodes?.results?.find((item) => item.id === allocatedNodeId)?.url;
  const allocatedNodeIp = allocatedNodeUrl?.split("://")?.[1]?.split(":")?.[0];

  const [createExchangeApiKey, createResults] = usePostExchangeApiKeyMutation();
  const [deleteExchangeApiKey, deleteResults] = useDeleteExchangeApiKeyMutation();

  const { formState, handleSubmit, register, reset, unregister } = useForm({
    defaultValues: { accessKey: "", passphrase: "", secretKey: "" },
    mode: "all",
  });
  const { errors, isValid } = formState;

  const onSubmit = async (data) => {
    setSubmitError(null);
    try {
      await createExchangeApiKey({
        access_key: data.accessKey,
        market_code: marketCodeForm.value,
        passphrase: marketCodeForm.exchange === "OKX" ? data.passphrase : undefined,
        secret_key: data.secretKey,
        trade_config_uuid: marketCodeCombination.tradeConfigUuid,
      }).unwrap();
      handleCloseDialog();
    } catch (error) {
      setSubmitError(error);
    }
  };

  const onDelete = useCallback(({ row }) => {
    setDeleteAlert({
      accessKey: row.original.access_key,
      id: row.original.uuid,
      trade_config_uuid: row.original.trade_config_uuid,
    });
  }, []);

  const columns = useMemo(
    () => [
      { accessorKey: "registered_at", header: t("Registration"), size: 100 },
      { accessorKey: "access_key", header: t("Access Key"), size: 120 },
      { accessorKey: "secret_key", header: t("Secret Key"), size: 50 },
      { accessorKey: "expires_at", header: t("Expiry"), size: 100 },
      {
        accessorKey: "icon",
        cell: renderActionIconCell,
        enableGlobalFilter: false,
        enableSorting: false,
        header: <span />,
        maxSize: 11,
        size: 11,
      },
    ],
    [t]
  );

  const tableData = useMemo(
    () => ({
      origin:
        exchangeApiKeys
          ?.filter((item) => item.market_code === marketCodeCombination.origin.value)
          .map((item) => ({
            ...item,
            access_key: truncate(item.access_key, { length: 40 }),
            registered_at: DateTime.fromISO(item.registered_datetime).toLocaleString(
              DateTime.DATETIME_MED
            ),
            secret_key: "●●●●●●",
          })) || [],
      target:
        exchangeApiKeys
          ?.filter((item) => item.market_code === marketCodeCombination.target.value)
          .map((item) => ({
            ...item,
            access_key: truncate(item.access_key, { length: 40 }),
            registered_at: DateTime.fromISO(item.registered_datetime).toLocaleString(
              DateTime.DATETIME_MED
            ),
            secret_key: "●●●●●●",
          })) || [],
    }),
    [exchangeApiKeys, marketCodeCombination]
  );

  useEffect(() => {
    if (marketCodeForm?.exchange !== "OKX") {
      unregister("passphrase");
    }
  }, [marketCodeForm?.exchange, unregister]);

  if (marketCodeCombination.value === "ALL") {
    return null;
  }

  return (
    <div className="legacy-surface legacy-surface--bot">
      <Grid container spacing={3} sx={{ px: { xs: 2, md: 4 } }}>
        <Grid item md={6} xs={12}>
          <Typography align="center">
            {marketCodeCombination.target.icon} {marketCodeCombination.target.getLabel()}
            <IconButton
              color="success"
              onClick={() => setMarketCodeForm(marketCodeCombination.target)}
              sx={{ ml: 2, p: 0 }}
            >
              <AddIcon />
            </IconButton>
          </Typography>
          <ReactTableUI
            columns={columns}
            data={tableData.target}
            getCellProps={() => ({
              sx: { py: 1, textAlign: "center", wordWrap: "break-word" },
            })}
            getHeaderProps={() => ({ sx: { textAlign: "center" } })}
            getTableProps={() => ({ sx: { mt: 2 } })}
            options={{
              meta: {
                action: {
                  icon: DeleteIcon,
                  iconProps: { color: "secondary" },
                  onClick: onDelete,
                },
              },
            }}
          />
        </Grid>
        <Grid item md={6} xs={12}>
          <Typography align="center">
            {marketCodeCombination.origin.icon} {marketCodeCombination.origin.getLabel()}
            <IconButton
              color="success"
              onClick={() => setMarketCodeForm(marketCodeCombination.origin)}
              sx={{ ml: 2, p: 0 }}
            >
              <AddIcon />
            </IconButton>
          </Typography>
          <ReactTableUI
            columns={columns}
            data={tableData.origin}
            getCellProps={() => ({
              sx: { py: 1, textAlign: "center", wordWrap: "break-word" },
            })}
            getHeaderProps={() => ({ sx: { textAlign: "center" } })}
            getTableProps={() => ({ sx: { mt: 2 } })}
            options={{
              meta: {
                action: {
                  icon: DeleteIcon,
                  iconProps: { color: "secondary" },
                  onClick: onDelete,
                },
              },
            }}
          />
        </Grid>
      </Grid>
      <Dialog
        fullWidth
        maxWidth="sm"
        open={!!marketCodeForm}
        onClose={handleCloseDialog}
        PaperProps={{
          autoComplete: "off",
          component: "form",
          onSubmit: handleSubmit(onSubmit),
        }}
      >
        <DialogTitle>
          {marketCodeForm?.icon} {marketCodeForm?.getLabel()} {t("API Key")}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {t("To activate trade features, please register your {{marketCode}} API Key", {
              marketCode: marketCodeForm?.getLabel() || "",
            })}
            .
          </DialogContentText>
          <DialogContentText>
            {t("When issuing an API key, please allow {{allocatedNodeIp}} for the access", {
              allocatedNodeIp: allocatedNodeIp || "",
            })}
            .
          </DialogContentText>
          <TextField
            autoFocus
            error={!!errors?.accessKey}
            fullWidth
            label={t("Access Key")}
            margin="dense"
            required
            variant="standard"
            {...register("accessKey", { required: true })}
          />
          <TextField
            error={!!errors?.secretKey}
            fullWidth
            inputProps={{ autoComplete: "off" }}
            label={t("Secret Key")}
            margin="dense"
            required
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle secret key visibility"
                      color="secondary"
                      onClick={() => setShowSecretKey((state) => !state)}
                      sx={{ p: 0 }}
                    >
                      {showSecretKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
            type={showSecretKey ? "text" : "password"}
            variant="standard"
            {...register("secretKey", { required: true })}
          />
          {marketCodeForm?.exchange === "OKX" ? (
            <TextField
              error={!!errors?.passphrase}
              fullWidth
              inputProps={{ autoComplete: "off" }}
              label={t("Passphrase")}
              margin="dense"
              required
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle passphrase visibility"
                        color="secondary"
                        onClick={() => setShowPassphrase((state) => !state)}
                        sx={{ p: 0 }}
                      >
                        {showPassphrase ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                },
              }}
              type={showPassphrase ? "text" : "password"}
              variant="standard"
              {...register("passphrase", { required: true })}
            />
          ) : null}
          {submitError ? (
            <Alert severity="error" sx={{ my: 2 }}>
              {(() => {
                if (submitError.status && submitError.data) {
                  if (submitError.status === 409) {
                    return t("API Key already exists");
                  }
                  if (typeof submitError.data?.detail === "string") {
                    return t(
                      "API key is not valid or IP permission is not set. Please check the API key and IP permission. error: {{error}}",
                      { error: submitError.data.detail }
                    );
                  }
                  return "An error occurred during submission.";
                }
                return t("Unknown error occurred. Contact the administrator");
              })()}
            </Alert>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button disabled={createResults.isLoading} onClick={handleCloseDialog}>
            {t("Cancel")}
          </Button>
          <Button disabled={!isValid || createResults.isLoading} type="submit">
            {t("Register")}
          </Button>
        </DialogActions>
      </Dialog>
      <DeleteAlert
        loading={deleteResults.isLoading}
        onCancel={() => setDeleteAlert(null)}
        onClose={() =>
          setDeleteAlert((current) => (deleteResults.isLoading ? current : null))
        }
        onDelete={async () => {
          await deleteExchangeApiKey(deleteAlert).unwrap();
          setDeleteAlert(null);
        }}
        open={!!deleteAlert}
        title={t(
          "Are you sure you want to permanently delete [{{accessKey}}...] API Key?",
          { accessKey: deleteAlert?.accessKey?.substring(0, 6) }
        )}
      />
    </div>
  );
}
