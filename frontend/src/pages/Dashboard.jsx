import { useEffect, useState } from "react";

import {
  approvePaper,
  rejectPaper,
  downloadQuestionPaper,
  getAuditLogs,
  getPendingPapers,
  getReleaseStatus,
  scheduleRelease,
  setupMFA,
  enableMFA,
  verifyAuditChain,
  uploadQuestionPaper,
} from "../services/api";

function Dashboard({
  user,
  onLogout,
}) {
  const isAuthority =
    user?.role === "EXAM_AUTHORITY";

  const [activeSection, setActiveSection] =
    useState(
      isAuthority
        ? "approvals"
        : "upload"
    );

  const [pendingPapers, setPendingPapers] =
    useState([]);

  const [auditLogs, setAuditLogs] =
    useState([]);

  const [auditStatus, setAuditStatus] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [message, setMessage] =
    useState("");

  const [error, setError] =
    useState("");

  const [releaseTimes, setReleaseTimes] =
    useState({});

  const [releaseStatuses, setReleaseStatuses] =
    useState({});

  const [uploadForm, setUploadForm] =
    useState({
      title: "",
      examination_name: "",
      subject: "",
      description: "",
      file: null,
    });

  const [rejectingPaperId, setRejectingPaperId] =
    useState(null);

  const [rejectionReason, setRejectionReason] =
    useState("");

  const [mfaSecret, setMfaSecret] =
    useState("");

  const [mfaUri, setMfaUri] =
    useState("");

  const [mfaCode, setMfaCode] =
    useState("");

  const [mfaMessage, setMfaMessage] =
    useState("");

  function clearFeedback() {
    setMessage("");
    setError("");
  }

  async function loadPendingPapers() {
    try {
      const data =
        await getPendingPapers();

      setPendingPapers(
        data.papers || []
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load pending papers."
      );
    }
  }

  async function loadAuditLogs() {
    try {
      const data =
        await getAuditLogs();

      setAuditLogs(
        data.logs || []
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load audit logs."
      );
    }
  }

  useEffect(() => {
    if (isAuthority) {
      loadPendingPapers();
    }
  }, [isAuthority]);

  async function handleUpload(event) {
    event.preventDefault();

    clearFeedback();
    setLoading(true);

    try {
      const formData =
        new FormData();

      formData.append(
        "title",
        uploadForm.title
      );

      formData.append(
        "examination_name",
        uploadForm.examination_name
      );

      formData.append(
        "subject",
        uploadForm.subject
      );

      formData.append(
        "description",
        uploadForm.description
      );

      formData.append(
        "file",
        uploadForm.file
      );

      const data =
        await uploadQuestionPaper(
          formData
        );

      setMessage(
        `Question paper #${data.question_paper.id} uploaded successfully and encrypted.`
      );

      setUploadForm({
        title: "",
        examination_name: "",
        subject: "",
        description: "",
        file: null,
      });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Question paper upload failed."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(id) {
    clearFeedback();

    try {
      await approvePaper(id);

      setMessage(
        `Question paper #${id} approved successfully.`
      );

      await loadPendingPapers();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Approval failed."
      );
    }
  }

  function openRejectDialog(id) {
    clearFeedback();
    setRejectingPaperId(id);
    setRejectionReason("");
  }

  function closeRejectDialog() {
    setRejectingPaperId(null);
    setRejectionReason("");
  }

  async function handleReject(event) {
    event.preventDefault();

    if (!rejectingPaperId) {
      return;
    }

    const reason = rejectionReason.trim();

    if (!reason) {
      setError("A rejection reason is required.");
      return;
    }

    clearFeedback();

    try {
      await rejectPaper(
        rejectingPaperId,
        reason
      );

      setMessage(
        `Question paper #${rejectingPaperId} rejected successfully.`
      );

      closeRejectDialog();
      await loadPendingPapers();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Rejection failed."
      );
    }
  }

  async function handleSchedule(id) {
    clearFeedback();

    const releaseAt =
      releaseTimes[id];

    if (!releaseAt) {
      setError(
        "Select a release date and time first."
      );
      return;
    }

    try {
      const iso =
        new Date(
          releaseAt
        ).toISOString();

      await scheduleRelease(
        id,
        iso
      );

      setMessage(
        `Question paper #${id} scheduled for controlled release.`
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Release scheduling failed."
      );
    }
  }

  async function handleReleaseStatus(id) {
    clearFeedback();

    try {
      const data =
        await getReleaseStatus(id);

      setReleaseStatuses(
        (current) => ({
          ...current,
          [id]: data.question_paper,
        })
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to retrieve release status."
      );
    }
  }

  async function handleDownload(id) {
    clearFeedback();

    try {
      const response =
        await downloadQuestionPaper(
          id
        );

      const blob =
        new Blob(
          [response.data],
          {
            type:
              "application/pdf",
          }
        );

      const url =
        window.URL.createObjectURL(
          blob
        );

      const link =
        document.createElement("a");

      link.href = url;
      link.download =
        `question-paper-${id}.pdf`;

      document.body.appendChild(
        link
      );

      link.click();

      link.remove();

      window.URL.revokeObjectURL(
        url
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Question paper is not available for download."
      );
    }
  }

  async function handleLoadAudit() {
    clearFeedback();

    await loadAuditLogs();
  }

  async function handleVerifyAudit() {
    clearFeedback();

    try {
      const data =
        await verifyAuditChain();

      setAuditStatus(data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Audit-chain verification failed."
      );
    }
  }

  async function handleMFASetup() {
    setMfaMessage("");

    try {
      const data =
        await setupMFA();

      setMfaSecret(
        data.secret
      );

      setMfaUri(
        data.provisioning_uri
      );

      setMfaMessage(
        "MFA setup generated. Add the account to your authenticator application."
      );
    } catch (err) {
      setMfaMessage(
        err.response?.data?.detail ||
          "Unable to initialize MFA."
      );
    }
  }

  async function handleMFAEnable() {
    try {
      const data =
        await enableMFA(
          mfaCode
        );

      setMfaMessage(
        data.message
      );

      setMfaSecret("");
      setMfaUri("");
      setMfaCode("");
    } catch (err) {
      setMfaMessage(
        err.response?.data?.detail ||
          "MFA activation failed."
      );
    }
  }

  const navItems = isAuthority
    ? [
        {
          id: "approvals",
          label: "Approvals",
          icon: "✓",
        },
        {
          id: "release",
          label: "Controlled Release",
          icon: "◷",
        },
        {
          id: "audit",
          label: "Audit & Transparency",
          icon: "◈",
        },
        {
          id: "mfa",
          label: "Security",
          icon: "◆",
        },
      ]
    : [
        {
          id: "upload",
          label: "Upload Paper",
          icon: "↑",
        },
        {
          id: "audit",
          label: "My Activity",
          icon: "◈",
        },
        {
          id: "mfa",
          label: "Security",
          icon: "◆",
        },
      ];

  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark small">
            SQ
          </div>

          <div>
            <strong>
              SecureQ
            </strong>

            <span>
              Examination System
            </span>
          </div>
        </div>

        <div className="sidebar-section-title">
          WORKSPACE
        </div>

        <nav className="sidebar-nav">
          {navItems.map(
            (item) => (
              <button
                key={item.id}
                className={
                  activeSection ===
                  item.id
                    ? "nav-item active"
                    : "nav-item"
                }
                onClick={() => {
                  clearFeedback();
                  setActiveSection(
                    item.id
                  );

                  if (
                    item.id ===
                    "approvals"
                  ) {
                    loadPendingPapers();
                  }

                  if (
                    item.id ===
                    "audit"
                  ) {
                    loadAuditLogs();
                  }
                }}
              >
                <span className="nav-icon">
                  {item.icon}
                </span>

                {item.label}
              </button>
            )
          )}
        </nav>

        <div className="sidebar-security">
          <div className="security-dot" />

          <div>
            <strong>
              Security active
            </strong>

            <span>
              Encrypted session
            </span>
          </div>
        </div>

        <button
          className="logout-button"
          onClick={onLogout}
        >
          Sign out
        </button>
      </aside>

      <main className="dashboard-main">
        <header className="topbar">
          <div>
            <span className="page-eyebrow">
              SECURE OPERATIONS
            </span>

            <h1>
              {activeSection ===
                "upload" &&
                "Question Paper Upload"}

              {activeSection ===
                "approvals" &&
                "Approval Control Center"}

              {activeSection ===
                "release" &&
                "Controlled Release"}

              {activeSection ===
                "audit" &&
                "Audit & Transparency"}

              {activeSection ===
                "mfa" &&
                "Security Settings"}
            </h1>
          </div>

          <div className="user-panel">
            <div className="user-avatar">
              {user?.full_name
                ?.charAt(0)
                .toUpperCase()}
            </div>

            <div>
              <strong>
                {user?.full_name}
              </strong>

              <span>
                {user?.role}
              </span>
            </div>
          </div>
        </header>

        {message && (
          <div className="success-banner">
            ✓ {message}
          </div>
        )}

        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}

        <section className="content-area">

          {/* ------------------------------------------------ */}
          {/* QUESTION SETTER UPLOAD */}
          {/* ------------------------------------------------ */}

          {activeSection ===
            "upload" && (
            <div className="content-grid">
              <div className="panel large">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">
                      SECURE INGESTION
                    </span>

                    <h2>
                      Upload Question Paper
                    </h2>
                  </div>

                  <span className="status-pill">
                    Encrypted
                  </span>
                </div>

                <form
                  className="paper-form"
                  onSubmit={
                    handleUpload
                  }
                >
                  <div className="form-row">
                    <label>
                      Paper Title
                      <input
                        value={
                          uploadForm.title
                        }
                        onChange={(
                          event
                        ) =>
                          setUploadForm(
                            {
                              ...uploadForm,
                              title:
                                event
                                  .target
                                  .value,
                            }
                          )
                        }
                        required
                      />
                    </label>

                    <label>
                      Examination
                      <input
                        value={
                          uploadForm.examination_name
                        }
                        onChange={(
                          event
                        ) =>
                          setUploadForm(
                            {
                              ...uploadForm,
                              examination_name:
                                event
                                  .target
                                  .value,
                            }
                          )
                        }
                        required
                      />
                    </label>
                  </div>

                  <div className="form-row">
                    <label>
                      Subject
                      <input
                        value={
                          uploadForm.subject
                        }
                        onChange={(
                          event
                        ) =>
                          setUploadForm(
                            {
                              ...uploadForm,
                              subject:
                                event
                                  .target
                                  .value,
                            }
                          )
                        }
                        required
                      />
                    </label>

                    <label>
                      Description
                      <input
                        value={
                          uploadForm.description
                        }
                        onChange={(
                          event
                        ) =>
                          setUploadForm(
                            {
                              ...uploadForm,
                              description:
                                event
                                  .target
                                  .value,
                            }
                          )
                        }
                      />
                    </label>
                  </div>

                  <label>
                    Question Paper PDF
                    <div className="file-drop">
                      <input
                        type="file"
                        accept=".pdf,application/pdf"
                        onChange={(
                          event
                        ) =>
                          setUploadForm(
                            {
                              ...uploadForm,
                              file:
                                event
                                  .target
                                  .files?.[0] ||
                                null,
                            }
                          )
                        }
                        required
                      />

                      <span>
                        {uploadForm.file
                          ? uploadForm
                              .file
                              .name
                          : "Select a PDF file"}
                      </span>
                    </div>
                  </label>

                  <div className="security-info-grid">
                    <div>
                      <strong>
                        AES-256-GCM
                      </strong>
                      <span>
                        File encryption
                      </span>
                    </div>

                    <div>
                      <strong>
                        SHA-256
                      </strong>
                      <span>
                        Integrity verification
                      </span>
                    </div>

                    <div>
                      <strong>
                        Audit
                      </strong>
                      <span>
                        Activity recorded
                      </span>
                    </div>
                  </div>

                  <button
                    className="primary-button"
                    type="submit"
                    disabled={
                      loading
                    }
                  >
                    {loading
                      ? "Encrypting & uploading..."
                      : "Securely upload paper"}
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* ------------------------------------------------ */}
          {/* APPROVALS */}
          {/* ------------------------------------------------ */}

          {activeSection ===
            "approvals" && (
            <div className="panel">
              <div className="panel-header">
                <div>
                  <span className="panel-kicker">
                    AUTHORITY CONTROL
                  </span>

                  <h2>
                    Pending Approvals
                  </h2>
                </div>

                <span className="count-badge">
                  {
                    pendingPapers.length
                  } pending
                </span>
              </div>

              {pendingPapers.length ===
              0 ? (
                <div className="empty-state">
                  <div className="empty-icon">
                    ✓
                  </div>

                  <h3>
                    No pending papers
                  </h3>

                  <p>
                    The approval queue is
                    currently clear.
                  </p>
                </div>
              ) : (
                <div className="paper-list">
                  {pendingPapers.map(
                    (paper) => (
                      <div
                        className="paper-card"
                        key={
                          paper.id
                        }
                      >
                        <div className="paper-number">
                          #
                          {
                            paper.id
                          }
                        </div>

                        <div className="paper-details">
                          <h3>
                            {
                              paper.title
                            }
                          </h3>

                          <p>
                            {
                              paper.examination_name
                            }
                          </p>

                          <span>
                            {
                              paper.subject
                            }
                          </span>
                        </div>

                        <span className="warning-pill">
                          PENDING
                        </span>

                        <button
                          className="approve-button"
                          onClick={() =>
                            handleApprove(
                              paper.id
                            )
                          }
                        >
                          Approve
                        </button>

                        <button
                          className="secondary-small-button"
                          onClick={() =>
                            openRejectDialog(
                              paper.id
                            )
                          }
                        >
                          Reject
                        </button>
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          )}

          {/* ------------------------------------------------ */}
          {/* RELEASE */}
          {/* ------------------------------------------------ */}

          {activeSection ===
            "release" && (
            <div className="panel">
              <div className="panel-header">
                <div>
                  <span className="panel-kicker">
                    CONTROLLED DISTRIBUTION
                  </span>

                  <h2>
                    Release Management
                  </h2>
                </div>
              </div>

              <div className="release-note">
                Only approved papers can be
                scheduled for controlled
                release.
              </div>

              {pendingPapers.length ===
              0 ? (
                <div className="empty-state">
                  <h3>
                    No pending approval
                    records
                  </h3>

                  <p>
                    Approved papers can be
                    managed using their
                    question-paper ID.
                  </p>
                </div>
              ) : (
                <div className="paper-list">
                  {pendingPapers.map(
                    (paper) => (
                      <div
                        className="release-card"
                        key={
                          paper.id
                        }
                      >
                        <div>
                          <h3>
                            #{paper.id}{" "}
                            {
                              paper.title
                            }
                          </h3>

                          <span>
                            {
                              paper.examination_name
                            }
                          </span>
                        </div>

                        <input
                          type="datetime-local"
                          value={
                            releaseTimes[
                              paper.id
                            ] || ""
                          }
                          onChange={(
                            event
                          ) =>
                            setReleaseTimes(
                              (
                                current
                              ) => ({
                                ...current,
                                [paper.id]:
                                  event
                                    .target
                                    .value,
                              })
                            )
                          }
                        />

                        <button
                          className="primary-small-button"
                          onClick={() =>
                            handleSchedule(
                              paper.id
                            )
                          }
                        >
                          Schedule
                        </button>

                        <button
                          className="secondary-small-button"
                          onClick={() =>
                            handleReleaseStatus(
                              paper.id
                            )
                          }
                        >
                          Check status
                        </button>

                        {releaseStatuses[
                          paper.id
                        ] && (
                          <div className="release-status">
                            State:{" "}
                            <strong>
                              {
                                releaseStatuses[
                                  paper.id
                                ]
                                  .release_state
                              }
                            </strong>
                          </div>
                        )}
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          )}

          {/* ------------------------------------------------ */}
          {/* AUDIT */}
          {/* ------------------------------------------------ */}

          {activeSection ===
            "audit" && (
            <div>
              <div className="audit-actions">
                <button
                  className="primary-button compact"
                  onClick={
                    handleLoadAudit
                  }
                >
                  Load audit trail
                </button>

                <button
                  className="secondary-button compact"
                  onClick={
                    handleVerifyAudit
                  }
                >
                  Verify hash chain
                </button>
              </div>

              {auditStatus && (
                <div
                  className={
                    auditStatus.valid
                      ? "chain-valid"
                      : "chain-invalid"
                  }
                >
                  <strong>
                    {auditStatus.valid
                      ? "✓ Audit chain verified"
                      : "⚠ Integrity violation detected"}
                  </strong>

                  <span>
                    {
                      auditStatus.message
                    }
                  </span>
                </div>
              )}

              <div className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">
                      ACCOUNTABILITY
                    </span>

                    <h2>
                      Security Audit Trail
                    </h2>
                  </div>
                </div>

                {auditLogs.length ===
                0 ? (
                  <div className="empty-state">
                    <h3>
                      No audit records
                      loaded
                    </h3>

                    <p>
                      Load the audit trail
                      to view recorded
                      security events.
                    </p>
                  </div>
                ) : (
                  <div className="audit-table-wrapper">
                    <table className="audit-table">
                      <thead>
                        <tr>
                          <th>
                            ID
                          </th>
                          <th>
                            User
                          </th>
                          <th>
                            Action
                          </th>
                          <th>
                            Resource
                          </th>
                          <th>
                            Details
                          </th>
                          <th>
                            Time
                          </th>
                        </tr>
                      </thead>

                      <tbody>
                        {auditLogs.map(
                          (log) => (
                            <tr
                              key={
                                log.id
                              }
                            >
                              <td>
                                #
                                {
                                  log.id
                                }
                              </td>

                              <td>
                                {
                                  log.user_id ??
                                  "SYSTEM"
                                }
                              </td>

                              <td>
                                <span className="action-tag">
                                  {
                                    log.action
                                  }
                                </span>
                              </td>

                              <td>
                                {log.resource_type ||
                                  "-"}
                                {log.resource_id
                                  ? ` #${log.resource_id}`
                                  : ""}
                              </td>

                              <td>
                                {
                                  log.details ||
                                  "-"
                                }
                              </td>

                              <td>
                                {new Date(
                                  log.created_at
                                ).toLocaleString()}
                              </td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {rejectingPaperId && (
            <div className="modal-backdrop">
              <div className="modal-card">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">
                      AUTHORITY CONTROL
                    </span>

                    <h2>
                      Reject Question Paper
                    </h2>
                  </div>
                </div>

                <p className="security-description">
                  Provide a reason for rejecting
                  question paper #{rejectingPaperId}.
                  The reason will be recorded in
                  the security audit trail.
                </p>

                <form
                  className="paper-form"
                  onSubmit={handleReject}
                >
                  <label>
                    Rejection Reason
                    <textarea
                      value={rejectionReason}
                      onChange={(event) =>
                        setRejectionReason(
                          event.target.value
                        )
                      }
                      placeholder="Enter the reason for rejection..."
                      rows="5"
                      required
                      autoFocus
                    />
                  </label>

                  <div className="audit-actions">
                    <button
                      type="button"
                      className="secondary-button compact"
                      onClick={closeRejectDialog}
                    >
                      Cancel
                    </button>

                    <button
                      type="submit"
                      className="primary-button compact"
                    >
                      Confirm rejection
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* ------------------------------------------------ */}
          {/* MFA */}
          {/* ------------------------------------------------ */}

          {activeSection ===
            "mfa" && (
            <div className="content-grid">
              <div className="panel large">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">
                      IDENTITY SECURITY
                    </span>

                    <h2>
                      Multi-Factor
                      Authentication
                    </h2>
                  </div>
                </div>

                <p className="security-description">
                  Protect the account with
                  time-based one-time password
                  authentication.
                </p>

                <button
                  className="primary-button"
                  onClick={
                    handleMFASetup
                  }
                >
                  Generate MFA setup
                </button>

                {mfaMessage && (
                  <div className="info-banner">
                    {mfaMessage}
                  </div>
                )}

                {mfaSecret && (
                  <div className="mfa-setup-box">
                    <h3>
                      Authenticator setup
                    </h3>

                    <p>
                      Add this secret to your
                      authenticator application.
                    </p>

                    <code>
                      {mfaSecret}
                    </code>

                    <p>
                      Provisioning URI:
                    </p>

                    <textarea
                      readOnly
                      value={mfaUri}
                    />

                    <label>
                      Enter the current
                      six-digit code
                      <input
                        value={
                          mfaCode
                        }
                        maxLength="6"
                        inputMode="numeric"
                        onChange={(
                          event
                        ) =>
                          setMfaCode(
                            event.target.value
                          )
                        }
                      />
                    </label>

                    <button
                      className="primary-button"
                      onClick={
                        handleMFAEnable
                      }
                      disabled={
                        mfaCode.length !==
                        6
                      }
                    >
                      Enable MFA
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default Dashboard;