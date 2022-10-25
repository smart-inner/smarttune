package create

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/smart-inner/smarttune/pkg/genericclioptions"
	"github.com/smart-inner/smarttune/util"
	"github.com/smart-inner/smarttune/util/http"
	"github.com/spf13/cobra"
	"html/template"
	"strings"
)

type CreateOptions struct {
	Backend      string
	System       string
	Target       string
	MoreIsBetter bool
	Algorithm    string
	TuningKnobs  []string
	SessionName  string

	genericclioptions.IOStreams
}

func NewCreateOptions(streams genericclioptions.IOStreams) *CreateOptions {
	return &CreateOptions{
		IOStreams: streams,
	}
}

func NewCmdCreate(streams genericclioptions.IOStreams) *cobra.Command {
	o := NewCreateOptions(streams)
	cmd := &cobra.Command{
		Use:   "create SESSION_NAME --backend=backend [--system=system] [--target=target]",
		Short: "Create session for the specified system",
		Long: `Create session, which include system type, system version, knobs catalog, metrics catalog
tuning algorithm and target objective.`,
		Run: func(cmd *cobra.Command, args []string) {
			util.CheckErr(o.Create(args))
		},
	}
	addCreateFlags(cmd, o)

	return cmd
}

func addCreateFlags(cmd *cobra.Command, opt *CreateOptions) {
	cmd.Flags().StringVar(&opt.Backend, "backend", "",
		"The backend <ip:port> for smarttune server, such as '127.0.0.1:5000'")
	cmd.Flags().StringVar(&opt.System, "system", "TiDB@v6.1.0",
		"The system for creating the session, such as 'TiDB@v6.1.0'")
	cmd.Flags().StringVar(&opt.Target, "target", "tidb.tidb_qps", "The target objective for tuning")
	cmd.Flags().BoolVar(&opt.MoreIsBetter, "more_is_better", true, "The strategy for target optimization")
	cmd.Flags().StringVar(&opt.Algorithm, "algo", "GPB", "The algorithm for tuning")
	cmd.Flags().StringSliceVar(&opt.TuningKnobs, "tuning_knobs", []string{}, "The knobs for tuning")
}

func (o *CreateOptions) CreateSession(url, session string) (string, error) {
	request := make(map[string]interface{})
	if err := json.Unmarshal([]byte(session), &request); err != nil {
		return "", err
	}
	resp, err := http.PostJSON(url, request)
	if err != nil {
		return "", err
	}
	return http.HandleResponse(resp)
}

func (o *CreateOptions) Create(args []string) error {
	if len(args) != 1 || len(o.Backend) == 0 {
		return errors.New(fmt.Sprintf("Error: invalid subcommand "+
			"'smartctl create %s --backend=%s'", strings.Join(args, " "), o.Backend))
	}
	smartTuneHome, err := util.GetHome()
	if err != nil {
		return err
	}
	sessionFile := fmt.Sprintf("%s/resource/templates/%s/session.json",
		smartTuneHome, strings.ToLower(o.System))
	o.SessionName = args[0]

	t, err := template.ParseFiles(sessionFile)
	if err != nil {
		return err
	}
	session := new(bytes.Buffer)
	if err = t.Execute(session, o); err != nil {
		return err
	}
	url := fmt.Sprintf("http://%s/api/session/create", o.Backend)
	out, err := o.CreateSession(url, session.String())
	if err != nil {
		return err
	}
	fmt.Fprintf(o.Out, out)
	return nil
}
